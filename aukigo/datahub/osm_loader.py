import logging

import overpass
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from overpass import UnknownOverpassError
from overpass.errors import ServerRuntimeError

from .models import Layer
from .utils import GeomType

logger = logging.getLogger(__name__)


class OsmLoader:
    # TODO: should Newer be used and should removed be deleted?
    QUERY_TEMPLATE = '''
// gather results
(
    // query parts
    {query_parts}
);
// print results
out body;
>;
    '''

    QUERY_PART_TEMPLATE = '''
    // query part for: {tag}
    node[{tag}]{bbox};
    way[{tag}]{bbox};
    relation[{tag}]{bbox};
    '''

    def __init__(self, timeout: int = 900):
        self.api = overpass.API(endpoint=settings.OVERPASS_API_URL, timeout=timeout)

    def populate(self, layer: Layer):
        """
        Populate models with features found by layer tags
        :param layer: Layer object
        :return:
        """
        ids = new_ids = set()

        for area in layer.areas.all():
            query_parts = [self.QUERY_PART_TEMPLATE.format(
                tag='"{}"="{}"'.format(*tag.split("=")),  # Tag in format "key=val", overpass wants "key"="val"
                bbox=area.overpass_bbox)
                for tag in layer.tags]
            query = self.QUERY_TEMPLATE.format(
                query_parts='\n'.join(query_parts),
            )
            logger.debug(query)
            try:
                data = self.api.get(query, verbosity='geom', responseformat='geojson')
            except (UnknownOverpassError, ServerRuntimeError, UnknownOverpassError):
                logger.exception(f"Query failed for following area: {area}. Skiping...")
                continue

            ids_, new_ids_ = self._geojson_to_objects(layer, data)
            ids = ids.union(ids_)
            new_ids = new_ids.union(new_ids_)

        logger.info(f"Processed {len(ids)} features. {len(new_ids)} new features.")

    @staticmethod
    def _geojson_to_objects(layer: Layer, data: {}):
        """
        Convert Geojson to model objects
        :param layer: Layer object
        :param data: in Geojson format
        :return:
        """
        tag_keys = {tag.split("=")[0] for tag in layer.tags}
        included_types = set()
        ids = set()
        new_ids = set()
        for feature in data['features']:
            osmid = feature['id']
            geom = GEOSGeometry(str(feature['geometry']), srid=settings.SRID)
            tags = feature['properties']
            geom_type = GeomType.from_feature(feature)

            # Point could belong to linestring or polygon
            if geom_type == GeomType.POINT and not len(tag_keys.intersection(tags.keys())):
                continue

            values = {'tags': tags, 'geom': geom}
            obj, created = geom_type.osm_model.objects.update_or_create(pk=osmid, defaults=values)

            if created:
                new_ids.add(osmid)
                logger.debug(f"New {geom_type.name} created: {osmid}")

            ids.add(osmid)
            obj.layers.add(layer)
            obj.save()
            included_types.add(geom_type)

        # Create views
        for geom_type in included_types:
            layer.create_view(geom_type)

        return ids, new_ids
