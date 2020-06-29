import os

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import OsmLayer, AreaOfInterest, OsmPoint, OsmLine, OsmPolygon
from .osm_loader import OsmLoader
from .utils import (overpass_bbox_to_polygon, polygon_to_overpass_bbox, osm_tags_to_dict, GeomType,
                    model_tag_to_overpass_tag)

TEST_POLYGON = Polygon(((24.499, 60.260), (24.499, 60.352), (24.668, 60.352), (24.668, 60.260), (24.499, 60.260)),
                       srid=settings.SRID)
TEST_BBOX = (60.260, 24.499, 60.352, 24.668)


class UtilsTests(TestCase):
    def setUp(self) -> None:
        self.polygon = TEST_POLYGON
        self.bbox = TEST_BBOX

    def test_overpass_bbox_to_polygon(self):
        polygon = overpass_bbox_to_polygon(self.bbox)
        self.assertEqual(polygon.extent, self.polygon.extent)

    def test_polygon_to_overpass_bbox(self):
        bbox = polygon_to_overpass_bbox(self.polygon)
        self.assertEqual(bbox, self.bbox)

    def test_osm_tags_to_dict(self):
        tag_string = '"1"=>"1","2"=>"long line with, commas"'
        tags = osm_tags_to_dict(tag_string)
        self.assertEqual(tags, {"1": "1", "2": "long line with, commas"})

    def test_model_tags_to_overpass_tags(self):
        tags = {"key=value", "key:value", "key~val.*", "~key~val", "key=*", "key"}
        expected = {'"key"="value"', '"key":"value"', '"key"~"val.*"', '"~key"~"val"', '"key"'}
        overpass_tags = {model_tag_to_overpass_tag(tag) for tag in tags}
        self.assertEqual(overpass_tags, expected)


@override_settings(VIEW_PREFIX='osm', PG_TILESERV_PORT=7800)
class ModelsTest(TestCase):

    def test_osmlayer_with_points(self):
        layer = OsmLayer.objects.create(name="test")
        layer.add_support_for_type(GeomType.POINT)
        layer.add_support_for_type(GeomType.POINT)
        self.assertEqual(layer.views, ["osm_test_p"])
        self.assertEqual(layer.tilesets.count(), 1)
        layer.delete()

    def test_osmlayer_with_multiple_types(self):
        layer = OsmLayer.objects.create(name="test")
        layer.add_support_for_type(GeomType.LINE)
        layer.add_support_for_type(GeomType.POINT)
        layer.add_support_for_type(GeomType.POLYGON)
        self.assertEqual(layer.views, ["osm_test_l", "osm_test_p", "osm_test_pl"])
        self.assertEqual(layer.tilesets.count(), 3)
        layer.delete()

    def test_api_serialization(self):
        layer = OsmLayer.objects.create(name="test")
        layer.add_support_for_type(GeomType.POINT)
        tileset = layer.tilesets.first()
        response = self.client.get(reverse("api-root") + f"tilesets/{tileset.pk}/").json()
        self.assertEqual(response,
                         {'url': f'http://testserver/api/tilesets/{tileset.pk}/', 'tilejson': '2.2.0', 'name': 'test',
                          'description': None, 'version': '1.0.0',
                          'attribution': "<a href='http://openstreetmap.org'>OSM contributors</a>",
                          'template': None,
                          'legend': None, 'scheme': 'xyz',
                          'tiles': ['http://testserver:7800/public.osm_test_p/{z}/{x}/{y}.pbf'], 'grids': [],
                          'data': [], 'minzoom': 1, 'maxzoom': 30, 'bounds': None,
                          'center': None}
                         )


class OsmLoadingTests(TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.polygon = TEST_POLYGON
        self.bbox = TEST_BBOX
        self.area = AreaOfInterest.objects.create(name="Test", bbox=self.polygon)
        self.layer = OsmLayer.objects.create(name="Camping", tags=["leisure=firepit"])
        self.layer.areas.add(self.area)
        self.layer.save()
        self.loader = OsmLoader()

    def test_with_firepit_points_multiple_times(self):
        features = self.loader._overpass_xml_to_geojson_features(read_json("firepit.osm"))
        self.assertEqual(len(features), 7)
        self.loader._synchronize_features(self.layer, self.area, features)
        ids, new_ids = self.loader._synchronize_features(self.layer, self.area, features)
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(new_ids), 0)
        self.assertEqual(OsmPoint.objects.first().layers.count(), 1)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 7)

    def test_with_hiking_routes(self):
        features = self.loader._overpass_xml_to_geojson_features(read_json("hiking_routes.osm"))
        self.assertEqual(len(features), 462)
        ids, new_ids = self.loader._synchronize_features(self.layer, self.area, features)
        self.assertEqual(len(ids), 462)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 67)
        lines_qs = OsmLine.objects.filter(layers=self.layer)
        self.assertEqual(lines_qs.count(), 395)
        self.assertEqual(lines_qs.filter(z_order__gt=1).count(), 69)

    def test_with_firepit_points(self):
        data = read_json("firepit.osm")

        features = self.loader._overpass_xml_to_geojson_features(data)
        self.assertEqual(len(features), 7)
        ids, new_ids = self.loader._synchronize_features(self.layer, self.area, features)
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(new_ids), 7)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 7)

        related = self.layer.get_related(self.layer.areas.first())
        self.assertEqual(related[GeomType.POINT],
                         {7505611520, 4623471079, 4623471080, 888747755, 2919437626, 7505611518, 7505611519})

        tileset = self.layer.tilesets.first()
        response = self.client.get(reverse("api-root") + f"tilesets/{tileset.pk}/").json()
        expected = {'url': f'http://testserver/api/tilesets/{tileset.pk}/', 'tilejson': '2.2.0', 'name': 'Camping',
                    'description': None, 'version': '1.0.0',
                    'attribution': "<a href='http://openstreetmap.org'>OSM contributors</a>",
                    'template': None,
                    'legend': None, 'scheme': 'xyz',
                    'tiles': ['http://testserver:7800/public.osm_camping_p/{z}/{x}/{y}.pbf'],
                    'grids': [],
                    'tags': ['leisure=firepit'],
                    'data': [], 'minzoom': 1, 'maxzoom': 30,
                    'bounds': [24.5552907, 60.2697246, 24.6639172, 60.3498801],
                    'center': [24.60960395, 60.309802350000005, 8]}
        self.assertEqual(response, expected)

    def test_with_administrative_boundary(self):
        features = self.loader._overpass_xml_to_geojson_features(read_json("administrative_boundary.osm"))
        ids, new_ids = self.loader._synchronize_features(self.layer, self.area, features)
        self.assertEqual(len(ids), 85)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 11)
        self.assertEqual(OsmLine.objects.filter(layers=self.layer).count(), 66)
        self.assertEqual(OsmPolygon.objects.filter(layers=self.layer).count(), 8)

    def test_with_deleted_features_removes_existing(self):
        features = self.loader._overpass_xml_to_geojson_features(read_json("firepit.osm"))
        self.loader._synchronize_features(self.layer, self.area, features)
        ids, new_ids = self.loader._synchronize_features(self.layer, self.area, features[:-2])
        self.assertEqual(len(ids), 5)
        self.assertEqual(len(new_ids), 0)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 5)

    def test_with_deleted_features_removes_existing2(self):
        features = self.loader._overpass_xml_to_geojson_features(read_json("firepit.osm"))
        self.loader._synchronize_features(self.layer, self.area, features)
        ids, new_ids = self.loader._synchronize_features(self.layer, self.area, [])
        self.assertEqual(ids, set())
        self.assertEqual(new_ids, set())
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 0)
        self.assertEqual(self.layer.tilesets.count(), 0)


# Helper functions
def read_json(fixture):
    with open(os.path.join(settings.TEST_DATA_DIR, fixture)) as f:
        data = f.read()
    return data
