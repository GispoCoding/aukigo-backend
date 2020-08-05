import logging
from typing import Tuple

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Extent
from django.contrib.gis.geos import Polygon
from django.contrib.postgres.fields import JSONField
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models import QuerySet
from django_better_admin_arrayfield.models.fields import ArrayField

from .utils import (GeomType, polygon_to_overpass_bbox)

logger = logging.getLogger(__name__)

DEFAULT_BOUNDS = (-180.0, -90.0, 180.0, 90.0)


class Layer(models.Model):
    # TileJSON spec static fields
    tilejson = "2.2.0"  # Describes the version of the TileJSON spec that is implemented by this JSON object
    scheme = "xyz"
    grids = []

    # TileJSON spec fields
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(max_length=1000, blank=True, null=True, help_text="OPTIONAL")
    version = models.CharField(max_length=10, default="1.0.0", blank=True,
                               help_text="OPTIONAL. A semver.org style version number. When changes across tiles are "
                                         "introduced, the minor version MUST change.")
    attribution = models.CharField(max_length=200, blank=True, null=True,
                                   help_text="OPTIONAL. Contains an attribution to be displayed when the map is shown to "
                                             "a user. Implementations MAY decide to treat this as HTML or literal text")
    template = models.TextField(max_length=1000, blank=True, null=True,
                                help_text="OPTIONAL. Contains a mustache template to be used to format data from grids "
                                          "for interaction. See https://github.com/mapbox/utfgrid-spec/tree/master/1.2 "
                                          "for the interactivity specification.")
    legend = models.CharField(max_length=200, blank=True, null=True,
                              help_text="OPTIONAL. Contains a legend to be displayed with the map. Implementations MAY "
                                        "decide to treat this as HTML or literal text.")
    minzoom = models.IntegerField(default=1, blank=True, help_text=">= 0, <= 30.")
    maxzoom = models.IntegerField(default=30, blank=True, help_text=">= 0, <= 30.")

    # Internal fields
    style = JSONField(blank=True, null=True, help_text="Mapbox Style JSON for all the vector layers")
    default_zoom = models.IntegerField(default=8, blank=True, help_text=">= 0, <= 30.")

    @property
    def data(self):
        return ""

    @property
    def osm_layer(self):
        return OsmLayer.objects.filter(name=self.name).first()

    def get_bounds(self, geom_type: GeomType) -> Tuple[float, float, float, float]:
        bounds = None
        osm_layer: OsmLayer = self.osm_layer
        if osm_layer:
            bounds = osm_layer.get_bounds(geom_type)
        return bounds if bounds else DEFAULT_BOUNDS

    def get_common_bounds(self) -> Tuple[float, float, float, float]:
        bounds = DEFAULT_BOUNDS
        osm_layer: OsmLayer = self.osm_layer
        if osm_layer:
            bounds = [sum(col) / float(len(col)) for col in
                      zip(*[self.get_bounds(geom_type) for geom_type in osm_layer.geom_types])]
        return bounds

    def get_center(self, geom_type: GeomType) -> Tuple[float, float, int]:
        bounds = self.get_bounds(geom_type)
        if bounds is not None:
            centroid = Polygon.from_bbox(bounds).centroid
            return centroid.x, centroid.y, self.default_zoom

    def get_common_center(self) -> Tuple[float, float, int]:
        bounds = self.get_common_bounds()
        if bounds is not None:
            centroid = Polygon.from_bbox(bounds).centroid
            return centroid.x, centroid.y, self.default_zoom

    def get_tags(self) -> [str]:
        osm_layer: OsmLayer = self.osm_layer
        tags = None
        if osm_layer:
            tags = osm_layer.tags
        return tags if tags is not None else []

    def get_geom_types(self) -> [GeomType]:
        osm_layer: OsmLayer = self.osm_layer
        geom_types = []
        if osm_layer:
            geom_types = osm_layer.geom_types
        return geom_types

    def get_vector_layers(self) -> [str]:
        osm_layer: OsmLayer = self.osm_layer
        vector_layers = []
        if osm_layer:
            vector_layers = osm_layer.views
        return vector_layers



    def __str__(self):
        return self.name


class AreaOfInterest(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    bbox = models.PolygonField(srid=settings.SRID, blank=True, null=True)

    @property
    def overpass_bbox(self):
        return polygon_to_overpass_bbox(self.bbox)

    def __str__(self):
        return self.name


class OsmLayer(Layer):
    """
    Base layer that will be shown to the client
    TODO: https://stackoverflow.com/a/26546181/10068922
    """
    tags = ArrayField(models.CharField(max_length=200), blank=True, null=True,
                      help_text="Allowed formats: key=val, key~regex, ~keyregex~regex, key=*, key")
    areas = models.ManyToManyField(AreaOfInterest, blank=True)

    # Use property geom_types for reading
    _geom_types = ArrayField(models.CharField(max_length=10), blank=True, null=True, default=list,
                             help_text="Leave this field empty. It is populated programmatically.")

    def delete(self, using=None, keep_parents=False):
        self._drop_views()
        return super().delete(using, keep_parents)

    def get_bounds(self, geom_type: GeomType) -> Tuple[float, float, float, float]:
        return self.get_objects_for_type(geom_type).aggregate(Extent('geom'))['geom__extent']

    def get_objects_for_type(self, geom_type: GeomType) -> QuerySet:
        return geom_type.osm_model.objects.filter(layers=self.pk)

    def get_related(self, area: AreaOfInterest) -> {GeomType: set}:
        bbox: Polygon = area.bbox.envelope
        return {
            GeomType.POINT: set(self.osmpoint_set.filter(geom__intersects=bbox).values_list('pk', flat=True)),
            GeomType.LINE: set(self.osmline_set.filter(geom__intersects=bbox).values_list('pk', flat=True)),
            GeomType.POLYGON: set(self.osmpolygon_set.filter(geom__intersects=bbox).values_list('pk', flat=True)),
        }

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
            view_name = self._get_view_name_for_type(geom_type)
            sql = f'CREATE OR REPLACE VIEW {view_name} AS {sql}'
            logger.debug(sql)
            with connection.cursor() as cursor:
                cursor.execute(sql, params)

            if self.attribution is None or "osm" not in self.attribution or "open" not in self.attribution.lower():
                self.attribution = "<a href='http://openstreetmap.org'>OSM contributors</a>"

            self._geom_types.append(geom_type.name)
            self.save()

            Tileset.objects.create(layer=self, table=view_name, geom_type=geom_type.name)

    def remove_support_from_type(self, geom_type: GeomType, using=DEFAULT_DB_ALIAS) -> None:
        """
        Removes support from geometry type
        :param geom_type:  geometry type to remove support from
        :param using: Database key
        :return:
        """

        if geom_type in self.geom_types:
            connection = connections[using]
            with connection.cursor() as cursor:
                sql = f'DROP VIEW IF EXISTS {self._get_view_name_for_type(geom_type)}'
                logger.debug(sql)
                cursor.execute(sql)

            self._geom_types.remove(geom_type.name)
            self.save()

            Tileset.objects.filter(layer=self, geom_type=geom_type.name).delete()

    def _get_view_name_for_type(self, geom_type: GeomType) -> str:
        return f"{settings.PG_VIEW_PREFIX}_{self.name.lower()}_{geom_type.value['postfix']}"

    def _drop_views(self):
        connection = connections[DEFAULT_DB_ALIAS]

        with connection.cursor() as cursor:
            for geom_type in self.geom_types:
                sql = f'DROP VIEW IF EXISTS {self._get_view_name_for_type(geom_type)}'
                logger.debug(sql)
                cursor.execute(sql)

    def __str__(self):
        return self.name


class Tileset(models.Model):
    """
    Serialized as Json following the TileJSON 2.2.0 Spec
    """

    # TileJSON spec static fields
    tilejson = "2.2.0"  # Describes the version of the TileJSON spec that is implemented by this JSON object
    scheme = "xyz"
    grids = []
    data = []

    # Internal fields
    layer = models.ForeignKey(Layer, related_name='tilesets', on_delete=models.CASCADE)
    table = models.CharField(max_length=50)
    geom_type = models.CharField(max_length=10)

    @property
    def g_type(self):
        return GeomType[self.geom_type]

    def __str__(self):
        return f"{self.layer} ({self.geom_type}): {self.table}"


class OsmFeature(models.Model):
    osmid = models.BigIntegerField(primary_key=True)
    layers = models.ManyToManyField(OsmLayer, blank=True)
    tags = JSONField()

    class Meta:
        abstract = True

    def remove_from_layer(self, layer: OsmLayer) -> None:
        """
        Remove layer from feature and delete it if it does not have any layers left
        :param layer: OsmLayer
        :return:
        """
        if layer in self.layers.all():
            self.layers.remove(layer)
            self.save()
        if self.layers.count() == 0:
            logger.debug(f"Deleted feature {self}")
            self.delete()


class OsmPoint(OsmFeature):
    geom = models.PointField(srid=settings.SRID)


class OsmLine(OsmFeature):
    geom = models.MultiLineStringField(srid=settings.SRID)
    z_order = models.IntegerField(default=0)


class OsmPolygon(OsmFeature):
    geom = models.MultiPolygonField(srid=settings.SRID)


class Basemap(models.Model):
    name = models.CharField(max_length=50)
    attribution = models.CharField(max_length=200, blank=True, null=True,
                                   help_text="OPTIONAL. Contains an attribution to be displayed when the map is shown to "
                                             "a user. Implementations MAY decide to treat this as HTML or literal text")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class WMTSBasemap(Basemap):
    url = models.URLField(max_length=500, help_text="Capabilities xml url")
    layer = models.CharField(max_length=100)
    tile_matrix_set = models.CharField(max_length=100)


class VectorTileBasemap(Basemap):
    url = models.URLField(max_length=1000, help_text="Vector tile url")
    api_key = models.CharField(max_length=200)

# Add other models here
