from django.conf import settings
from rest_framework import serializers

from .models import Tileset, AreaOfInterest, OsmLayer, WMTSBasemap, VectorTileBasemap


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
