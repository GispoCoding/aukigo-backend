import json
import os

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.test import TestCase

from .models import Layer, AreaOfInterest, OsmPoint, OsmLine
from .osm_loader import OsmLoader
from .utils import overpass_bbox_to_polygon, polygon_to_overpass_bbox

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


class OsmLoadingTests(TestCase):
    def setUp(self) -> None:
        self.polygon = TEST_POLYGON
        self.bbox = TEST_BBOX
        area = AreaOfInterest.objects.create(name="Test", bbox=self.polygon)
        self.layer = Layer.objects.create(name="Camping", tags=["leisure=firepit"], is_osm_layer=True)
        self.layer.areas.add(area)
        self.layer.save()
        self.loader = OsmLoader()

    def test_data_conversion_with_firepit_points(self):
        with open(os.path.join(settings.TEST_DATA_DIR, "firepit.json")) as f:
            data = json.load(f)
        ids, new_ids = self.loader._geojson_to_objects(self.layer, data)
        self.assertEqual(len(ids), 7)
        self.assertEqual(len(new_ids), 7)
        self.assertEqual(OsmPoint.objects.filter(layers=self.layer).count(), 7)

    def test_data_processing_with_hiking_routes(self):
        with open(os.path.join(settings.TEST_DATA_DIR, "hiking_routes.json")) as f:
            data = json.load(f)
        ids, new_ids = self.loader._geojson_to_objects(self.layer, data)
        self.assertEqual(len(ids), 382)
        self.assertEqual(OsmLine.objects.filter(layers=self.layer).count(), 382)
