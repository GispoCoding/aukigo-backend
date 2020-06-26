import logging
from unittest.mock import patch

from django.test import TestCase, tag, override_settings

from .exeptions import TooManyRequests
from .models import OsmPoint, Tileset
from .tasks import load_osm_data

logging.disable(logging.DEBUG)


def mocked_exception(*args, **kwargs):
    raise TooManyRequests()


@tag("integration")  # ./manage.py test --exclude-tag=integration & ./manage.py test --tag=integration
@override_settings(IN_INTEGRATION_TEST=True)
class DatahubIntegrationTests(TestCase):
    # names: camping, tourism, tourism2
    fixtures = ['camping.json']

    def test_load_osm_data(self):
        # This test expects working internet connection to download data trough Overpass API
        load_osm_data()
        self.assertGreater(OsmPoint.objects.filter(layers__name='camping').count(), 2)
        self.assertGreater(OsmPoint.objects.filter(layers__name='tourism').count(), 0)  # contains regex tag
        self.assertGreater(OsmPoint.objects.filter(layers__name='tourism2').count(), 6)  # contains two tags

        self.assertGreater(Tileset.objects.count(), 3)  # At least one geom type for each

    @patch("datahub.osm_loader.OsmLoader.populate", side_effect=mocked_exception)
    def test_load_osm_retries_when_error_occurs(self, mocked_loader):
        # This test probably expects that Celery is running
        load_osm_data()
        self.assertEqual(mocked_loader.call_count, 15)  # (1 original + 4 retries) * 3
