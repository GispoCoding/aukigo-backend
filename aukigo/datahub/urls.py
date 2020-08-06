from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from .views import (is_authenticated, start_osm_task, TilesetViewSet, AreaViewSet, OsmLayerViewSet, WMTSBasemapViewSet,
                    VectorTileBasemapViewSet, Capabilities, LayerViewSet, OsmGeojsons)

router = routers.DefaultRouter()
router.register(r'OsmLayers', OsmLayerViewSet)
router.register(r'layers', LayerViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'tilesets', TilesetViewSet)
router.register(r'basemaps-wmts', WMTSBasemapViewSet)
router.register(r'basemaps-vt', VectorTileBasemapViewSet)


urlpatterns = [
    url(r'^', include(router.urls), name="api_root"),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('is_authenticated/', is_authenticated),
    path('populate_osm/', start_osm_task),
    path('capabilities/', Capabilities.as_view(), name='capabilities'),
    path('osm_geojson/<int:layer>/<str:gtype>.geojson', OsmGeojsons.as_view(), name='osm_geojsons')
]
