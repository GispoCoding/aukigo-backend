import logging

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.db import DEFAULT_DB_ALIAS, connections
from django_better_admin_arrayfield.models.fields import ArrayField

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
    tags = ArrayField(models.CharField(max_length=200), blank=True, null=True,
                      help_text="Allowed formats: key=val, key:valuefragment, "
                                "key~regex, ~keyregex~regex, key=*, key")
    is_osm_layer = models.BooleanField()
    areas = models.ManyToManyField(AreaOfInterest, blank=True)

    # Use property geom_types for reading
    _geom_types = ArrayField(models.CharField(max_length=10), blank=True, null=True, default=list,
                             help_text="Leave this field empty. It is populated programmatically.")

    def delete(self, using=None, keep_parents=False):
        if self.is_osm_layer:
            self._drop_view()
        return super().delete(using, keep_parents)

    @property
    def views(self) -> [str]:
        return [self._get_view_name_for_type(geom_type) for geom_type in self.geom_types]

    @property
    def geom_types(self) -> [GeomType]:
        if self._geom_types is None:
            self._geom_types = []
            self.save()
        return [GeomType[gtype] for gtype in self._geom_types]

    def add_support_for_type(self, geom_type: GeomType, using=DEFAULT_DB_ALIAS) -> None:
        """
        Adds view and type for geometry type
        :param geom_type: geometry type to support
        :param using: Database key
        :return:
        """
        # Inspired by https://adamj.eu/tech/2019/04/29/create-table-as-select-in-django/
        if geom_type not in self.geom_types:
            queryset = geom_type.osm_model.objects.filter(layers=self)
            compiler = queryset.query.get_compiler(using=using)
            sql, params = compiler.as_sql()
            connection = connections[DEFAULT_DB_ALIAS]
            sql = sql.replace('::bytea', '')  # Use geom as is, do not convert it to byte array
            sql = f'CREATE OR REPLACE VIEW {self._get_view_name_for_type(geom_type)} AS {sql}'
            logger.debug(sql)
            with connection.cursor() as cursor:
                cursor.execute(sql, params)

            self._geom_types.append(geom_type.name)
            self.save()

    def _get_view_name_for_type(self, geom_type: GeomType):
        return f"{settings.PG_VIEW_PREFIX}_{self.name.lower()}_{geom_type.value['postfix']}"

    def _drop_view(self):
        connection = connections[DEFAULT_DB_ALIAS]

        with connection.cursor() as cursor:
            for geom_type in self.geom_types:
                sql = f'DROP VIEW IF EXISTS {self._get_view_name_for_type(geom_type)}'
                logger.debug(sql)
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
    geom = models.MultiLineStringField(srid=settings.SRID)
    z_order = models.IntegerField(default=0)


class OsmPolygon(OsmFeature):
    geom = models.MultiPolygonField(srid=settings.SRID)

# Add other models here
