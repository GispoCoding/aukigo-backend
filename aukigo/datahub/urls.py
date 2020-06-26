from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from .views import is_authenticated, start_osm_task, TilesetViewSet, AreaViewSet, OsmLayerViewSet

router = routers.DefaultRouter()
router.register(r'OsmLayers', OsmLayerViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'tilesets', TilesetViewSet)

urlpatterns = [
    url(r'^', include(router.urls), name="api_root"),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('is_authenticated/', is_authenticated),
    path('populate_osm/', start_osm_task),
]
