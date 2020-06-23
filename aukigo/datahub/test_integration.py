import logging

from django.test import TestCase, tag

from .models import OsmPoint
from .tasks import load_osm_data

logging.disable(logging.DEBUG)


@tag("integration")  # ./manage.py test --exclude-tag=integration & ./manage.py test --tag=integration
class DatahubIntegrationTests(TestCase):
    # names: camping, tourism, tourism2
    fixtures = ['camping.json']

    def test_load_osm_data(self):
        # This test expects working internet connection to download data trough Overpass API
        load_osm_data()
        self.assertGreater(OsmPoint.objects.filter(layers__name='camping').count(), 2)
        self.assertGreater(OsmPoint.objects.filter(layers__name='tourism').count(), 0)  # contains regex tag
        self.assertGreater(OsmPoint.objects.filter(layers__name='tourism2').count(), 6)  # contains two tags
