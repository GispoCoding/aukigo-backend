from django.conf import settings
from django.urls import reverse
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (Tileset, AreaOfInterest, OsmLayer, WMTSBasemap, VectorTileBasemap,
                     Layer, OsmPoint, OsmPolygon, OsmLine)


class OsmLayerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OsmLayer
        exclude = ('_geom_types',)


class AreaOfInterestSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AreaOfInterest
        fields = ('url', 'name', 'bbox')


class TilesetSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.ReadOnlyField(source='layer.name')
    description = serializers.ReadOnlyField(source='layer.description')
    version = serializers.ReadOnlyField(source='layer.version')
    attribution = serializers.ReadOnlyField(source='layer.attribution')
    template = serializers.ReadOnlyField(source='layer.template')
    legend = serializers.ReadOnlyField(source='layer.legend')
    minzoom = serializers.ReadOnlyField(source='layer.minzoom')
    maxzoom = serializers.ReadOnlyField(source='layer.maxzoom')

    tiles = serializers.SerializerMethodField()
    bounds = serializers.SerializerMethodField()
    center = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_tiles(self, instance):
        request = self.context['request']
        pg_tileserv_url = "{sheme}://{host}{postfix}".format(
            sheme=request.scheme,
            host=request.get_host().split(":")[0],
            postfix=settings.PG_TILESERV_POSTFIX
        )
        vector_props = "{z}/{x}/{y}.pbf"
        tileurl = f"{pg_tileserv_url}/public.{instance.table}/{vector_props}"
        return [tileurl]

    def get_bounds(self, instance):
        return instance.layer.get_bounds(instance.g_type)

    def get_center(self, instance):
        return instance.layer.get_center(instance.g_type)

    def get_tags(self, instance):
        return instance.layer.get_tags()

    class Meta:
        model = Tileset
        fields = (
            'url', 'tilejson', 'name', 'description', 'version', 'attribution', 'template', 'legend', 'scheme',
            'tiles', 'grids', 'tags', 'data', 'minzoom', 'maxzoom', 'bounds', 'center'
        )


class LayerSerializer(serializers.HyperlinkedModelSerializer):
    tiles = serializers.SerializerMethodField()
    bounds = serializers.SerializerMethodField()
    center = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    vector_layers = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    def get_tiles(self, instance):
        request = self.context['request']
        pg_tileserv_url = "{sheme}://{host}{postfix}".format(
            sheme=request.scheme,
            host=request.get_host().split(":")[0],
            postfix=settings.PG_TILESERV_POSTFIX
        )
        vector_props = "{z}/{x}/{y}.pbf"
        tileurls = [f"{pg_tileserv_url}/public.{layer}/{vector_props}" for layer in self.get_vector_layers(instance)]
        return tileurls

    def get_bounds(self, instance):
        return instance.get_common_bounds()

    def get_center(self, instance):
        return instance.get_common_center()

    def get_tags(self, instance):
        return instance.get_tags()

    def get_vector_layers(self, instance):
        return instance.get_vector_layers()

    def get_data(self, instance):
        r: Request = self.context['request']
        host = f"{r.scheme}://{r.get_host()}"
        return [host + reverse('osm_geojsons', kwargs={'layer': instance.pk, 'gtype': geom_type.name}) for
                geom_type in instance.get_geom_types()]

    class Meta:
        model = Layer
        fields = (
            'url', 'tilejson', 'name', 'description', 'version', 'attribution', 'template', 'legend', 'scheme',
            'tiles', 'grids', 'tags', 'data', 'minzoom', 'maxzoom', 'bounds', 'center', 'vector_layers', 'style'
        )


class BasemapSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'attribution', 'url')
        abstract = True


class WTMSBasemapSerializer(BasemapSerializer):
    class Meta:
        fields = BasemapSerializer.Meta.fields + ('layer', 'tile_matrix_set')
        model = WMTSBasemap


class VectorTileBasemapSerializer(BasemapSerializer):
    class Meta:
        fields = BasemapSerializer.Meta.fields + ('api_key',)
        model = VectorTileBasemap


class OsmPointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = OsmPoint
        exclude = ('layers',)
        geo_field = "geom"


class OsmLineSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = OsmLine
        exclude = ('layers',)
        geo_field = "geom"


class OsmPolygonSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = OsmPolygon
        exclude = ('layers',)
        geo_field = "geom"
