import logging

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models import QuerySet

from .apps import DatahubConfig
from .utils import GeomType, polygon_to_overpass_bbox

logger = logging.getLogger(__name__)


class AreaOfInterest(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    bbox = models.PolygonField(srid=settings.SRID, blank=True, null=True)

    @property
    def overpass_bbox(self):
        return polygon_to_overpass_bbox(self.bbox)

    def __str__(self):
        return self.name


class Layer(models.Model):
    """
    Base layer that will be shown to the client
    TODO: https://stackoverflow.com/a/26546181/10068922
    """
    name = models.CharField(max_length=200)
    tags = ArrayField(models.CharField(max_length=200), blank=True, null=True)
    is_osm_layer = models.BooleanField()
    areas = models.ManyToManyField(AreaOfInterest, blank=True)

    def view_name(self, geom_type: GeomType):
        return f"{DatahubConfig.name}_{self.name.lower()}_{geom_type.value['postfix']}"

    def delete(self, using=None, keep_parents=False):
        if self.is_osm_layer:
            self.drop_view()
        return super().delete(using, keep_parents)

    def create_view(self, geom_type: GeomType, using=DEFAULT_DB_ALIAS):
        # Inspired by https://adamj.eu/tech/2019/04/29/create-table-as-select-in-django/
        queryset = geom_type.osm_model.objects.filter(layers=self)
        compiler = queryset.query.get_compiler(using=using)
        sql, params = compiler.as_sql()
        connection = connections[DEFAULT_DB_ALIAS]
        sql = sql.replace('::bytea', '')
        sql = f'CREATE OR REPLACE VIEW {self.view_name(geom_type)} AS {sql}'
        logger.debug(sql)
        with connection.cursor() as cursor:
            cursor.execute(sql, params)

    def drop_view(self):
        connection = connections[DEFAULT_DB_ALIAS]
        sql = f'DROP VIEW IF EXISTS {self.view_name}'
        with connection.cursor() as cursor:
            cursor.execute(sql)

    def __str__(self):
        return self.name


class OsmFeature(models.Model):
    osmid = models.BigIntegerField(primary_key=True)
    layers = models.ManyToManyField(Layer, blank=True)
    tags = JSONField()

    class Meta:
        abstract = True


class OsmPoint(OsmFeature):
    geom = models.PointField(srid=settings.SRID)


class OsmLine(OsmFeature):
    geom = models.LineStringField(srid=settings.SRID)


class OsmPolygon(OsmFeature):
    geom = models.MultiPolygonField(srid=settings.SRID)

# Add other models here
