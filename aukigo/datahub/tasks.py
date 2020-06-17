import logging

from celery import shared_task
from .models import Layer
from .osm_loader import OsmLoader

logger = logging.getLogger(__name__)


@shared_task
def load_osm_data():
    loader = OsmLoader()
    try:
        for layer in Layer.objects.filter(is_osm_layer=True):
            loader.populate(layer)
    except Exception:
        logger.exception("Uncaught error occurred while loading osm data")
        raise ()
