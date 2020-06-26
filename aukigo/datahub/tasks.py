import logging

from celery import shared_task, group
from django.conf import settings

from .exeptions import TooManyRequests
from .models import OsmLayer, AreaOfInterest
from .osm_loader import OsmLoader

logger = logging.getLogger(__name__)


@shared_task
def load_osm_data():
    """
    Task to load OSM data into the database for each layer.
    Spawns number of retryable child tasks
    :return:
    """
    g = group(load_osm_data_for_area.s(layer.pk, area.pk)
              for layer in OsmLayer.objects.all()
              for area in layer.areas.all())

    if not settings.IN_INTEGRATION_TEST:
        # Using queue with concurrency of 1 to avoid problems with the Overpass API
        g.apply_async(queue='network')
    else:
        g.apply()


@shared_task(rate_limit='10/s', autoretry_for=(TooManyRequests,), retry_backoff=2, retry_backoff_max=60,
             max_retries=4)
def load_osm_data_for_area(layer_id, area_id):
    """
    Load OSM data for given layer and area
    :param layer_id: OsmLayer pk
    :param area_id: AreaOfInterest pk
    :return: completion status
    """
    loader = OsmLoader()
    layer = OsmLayer.objects.get(pk=layer_id)
    area = AreaOfInterest.objects.get(pk=area_id)

    try:
        succeeded = loader.populate(layer, area)
        return succeeded
    except Exception:
        logger.exception("Uncaught error occurred while loading osm data")
        raise
