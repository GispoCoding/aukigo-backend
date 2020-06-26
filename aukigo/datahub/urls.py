from django.conf.urls import url
from django.urls import path, include
from rest_framework import routers

from .views import is_authenticated, start_osm_task, TilesetViewSet

router = routers.DefaultRouter()
router.register(r'tilesets', TilesetViewSet)

urlpatterns = [
    url(r'^', include(router.urls), name="api_root"),
    path('is_authenticated/', is_authenticated),
    path('populate_osm/', start_osm_task),
]
