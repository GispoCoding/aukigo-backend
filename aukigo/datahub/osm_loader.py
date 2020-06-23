import json
import logging
import os
import tempfile
from typing import Tuple, Set

import requests
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from osgeo import gdal

from .exeptions import TooManyRequests
from .models import Layer, AreaOfInterest
from .utils import GeomType, osm_tags_to_dict, model_tag_to_overpass_tag

logger = logging.getLogger(__name__)


class OsmLoader:
    URL = f"{settings.OVERPASS_API_URL}/interpreter"
    KILL_EXISTING_QUERIES_URL = f"{settings.OVERPASS_API_URL}/kill_my_queries"
    # TODO: should Newer be used and should removed be deleted?
    QUERY_TEMPLATE = '''
// gather results
[out:xml][timeout:{timeout}];
(
    // query parts
    {query_parts}
);
// print results
(._;>;);out body;
    '''

    QUERY_PART_TEMPLATE = '''
    // query part for: {tag}
    node[{tag}]{bbox};
    way[{tag}]{bbox};
    relation[{tag}]{bbox};
    '''

    def __init__(self, timeout: int = 900):
        """

        :param timeout: Timeout for the query execution
        """
        self.timeout = timeout

    def populate(self, layer: Layer, area: AreaOfInterest) -> bool:
        """
        Populate models with features found by layer tags
        :param layer: Layer object
        :param area: AreaOfInterest object from layer
        :return: Whether any features were populated or not
        """

        query_parts = [self.QUERY_PART_TEMPLATE.format(
            tag=model_tag_to_overpass_tag(tag),
            bbox=area.overpass_bbox
        )
            for tag in layer.tags]
        if not len(query_parts):
            logger.debug("No tags available, skipping...")
            return False

        query = self.QUERY_TEMPLATE.format(
            query_parts='\n'.join(query_parts),
            timeout=self.timeout
        )
        logger.debug(query)

        r = requests.get(self.URL, params={'data': query})
        try:
            if r.status_code == 426:
                # Too many requests, killing existing with instructions
                # from http://overpass-api.de/command_line.html and retrying using Celery
                logger.warning(f"Too many requests foor {layer}:{area}, killing existing and retrying...")
                requests.get(self.KILL_EXISTING_QUERIES_URL)
                raise TooManyRequests()

            r.raise_for_status()
            features = self._overpass_xml_to_geojson_features(r.text)
        except requests.HTTPError:
            logger.exception(
                f"Query failed for following area: '{area}'. Query: {query} \n Headers: {r.headers} \n Skpping...")
            return False

        ids, new_ids = self._save_features(layer, features)

        logger.info(f"Processed layer '{layer}': {len(ids)} features. {len(new_ids)} new features.")
        return len(ids) > 0

    @staticmethod
    def _overpass_xml_to_geojson_features(xml_data: str) -> []:
        """
        Converts Overpass xml to geojson features
        :param xml_data: Overpass XML
        :return: list of features
        """

        ogr2ogr_params = [
            "-a_srs", f"EPSG:4326",
        ]

        ogr2ogr_multi_params = ogr2ogr_params + ["-nlt", "PROMOTE_TO_MULTI"]

        gdal.SetConfigOption('OSM_CONFIG_FILE', settings.OSM_CONFIG)
        gdal.SetConfigOption('OSM_USE_CUSTOM_INDEXING', 'NO')

        features = []

        with tempfile.TemporaryDirectory() as tmpdirname:
            xml_fil_path = os.path.join(tmpdirname, "data.osm")
            with open(xml_fil_path, "w") as f:
                f.write(xml_data)

            for geom_type in list(GeomType):
                layers = geom_type.value['osm_layers']
                for layer in layers:
                    params = ogr2ogr_params if geom_type == GeomType.POINT else ogr2ogr_multi_params

                    layer_fil = os.path.join(tmpdirname, f"layer.json")
                    try:
                        gdal.VectorTranslate(
                            layer_fil, xml_fil_path,
                            options=f'{layer} -f GeoJSON ' + ' '.join(params)
                        )
                        with open(layer_fil) as f:
                            geojson = json.load(f)
                            features += geojson["features"]
                    except RuntimeError:
                        logger.exception("Could not translate OSM file to geojson. Skipping...")

        return features

    @staticmethod
    def _save_features(layer: Layer, features: []) -> Tuple[Set, Set]:
        """
        Save Geojson features as model objects
        :param layer: Layer object
        :param features: in Geojson format
        :return: all ids and new ids as sets
        """
        included_types = set()
        ids = set()
        new_ids = set()
        for feature in features:
            props = feature['properties']
            # if osm_way_id is present, it represents that the geometry is closed way instead of relation
            osmid = int(props.get('osm_id', props.get('osm_way_id')))
            geom = GEOSGeometry(str(feature['geometry']), srid=settings.SRID)
            tags = osm_tags_to_dict(props["all_tags"])
            geom_type = GeomType.from_feature(feature)

            values = {'tags': tags, 'geom': geom}
            if geom_type == GeomType.LINE:
                values["z_order"] = props.get("z_order", 0)

            obj, created = geom_type.osm_model.objects.update_or_create(pk=osmid, defaults=values)

            if created:
                new_ids.add(osmid)
                logger.debug(f"New {geom_type.name} created: {osmid}")

            ids.add(osmid)
            if layer not in obj.layers.all():
                obj.layers.add(layer)
                obj.save()
            included_types.add(geom_type)

        # Create views
        for geom_type in included_types:
            layer.add_support_for_type(geom_type)

        return ids, new_ids
