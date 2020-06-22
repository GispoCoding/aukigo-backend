import os

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Layer, AreaOfInterest, OsmPoint, OsmLine, OsmPolygon
from .osm_loader import OsmLoader
from .utils import overpass_bbox_to_polygon, polygon_to_overpass_bbox, osm_tags_to_dict, GeomType

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


@override_settings(VIEW_PREFIX='osm', PG_TILESERV_PORT=7800)
class ModelsTest(TestCase):

    def test_layer_with_points(self):
        layer = Layer.objects.create(name="test", is_osm_layer=True)
        layer.add_support_for_type(GeomType.POINT)
        layer.add_support_for_type(GeomType.POINT)
        self.assertEqual(layer.views, ["osm_test_p"])
        layer.delete()

    def test_layer_with_multiple_types(self):
        layer = Layer.objects.create(name="test", is_osm_layer=True)
        layer.add_support_for_type(GeomType.LINE)
        layer.add_support_for_type(GeomType.POINT)
        layer.add_support_for_type(GeomType.POLYGON)
        self.assertEqual(layer.views, ["osm_test_l", "osm_test_p", "osm_test_pl"])
        layer.delete()

    def test_capabilities_view(self):
        layer = Layer.objects.create(name="test", is_osm_layer=True)
        layer.add_support_for_type(GeomType.POINT)
        Layer.objects.create(name="non_osm", is_osm_layer=False)
        capabilities = self.client.get(reverse("capabilities")).json()
        self.assertEqual(capabilities["layers"][0]["urls"],
                         [{'config': 'http://testserver:7800/public.osm_test_p.json',
                           'tile': 'http://testserver:7800/public.osm_test_p/{z}/{x}/{y}.pbf?properties=osmid,tags'}])
        self.assertEqual(capabilities["layers"][1]["urls"],
                         [{'config': 'http://testserver:7800/public.non_osm.json',
                           'tile': 'http://testserver:7800/public.non_osm/{z}/{x}/{y}.pbf'}])


class OsmLoadingTests(TestCase):
    def setUp(self) -> None:
        self.polygon = TEST_POLYGON
        self.bbox = TEST_BBOX
        area = AreaOfInterest.objects.create(name="Test", bbox=self.polygon)
        self.layer = Layer.objects.create(name="Camping", tags=["leisure=firepit"], is_osm_layer=True)
        self.layer.areas.add(area)
        self.layer.save()
        self.loader = OsmLoader()

    def test_osm_data_processing_with_firepit_points(self):
        with open(os.path.join(settings.TEST_DATA_DIR, "firepit.osm")) as f:
            data = f.read()

        features = self.loader._overpass_xml_to_geojson_features(data)
        self.assertEqual(len(features), 7)
        ids, new_ids = self.loader._save_features(self.layer, features)
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(new_ids), 7)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 7)

    def test_osm_data_processing_with_hiking_routes(self):
        with open(os.path.join(settings.TEST_DATA_DIR, "hiking_routes.osm")) as f:
            data = f.read()
        features = self.loader._overpass_xml_to_geojson_features(data)
        self.assertEqual(len(features), 462)
        ids, new_ids = self.loader._save_features(self.layer, features)
        self.assertEqual(len(ids), 462)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 67)
        self.assertEqual(OsmLine.objects.filter(layers=self.layer).count(), 395)

    def test_osm_data_processing_with_administrative_boundary(self):
        with open(os.path.join(settings.TEST_DATA_DIR, "administrative_boundary.osm")) as f:
            data = f.read()
        features = self.loader._overpass_xml_to_geojson_features(data)
        ids, new_ids = self.loader._save_features(self.layer, features)
        self.assertEqual(len(ids), 85)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 11)
        self.assertEqual(OsmLine.objects.filter(layers=self.layer).count(), 66)
        self.assertEqual(OsmPolygon.objects.filter(layers=self.layer).count(), 8)
