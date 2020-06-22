from django.urls import path

from .views import Capabilities, is_authenticated, start_osm_task

urlpatterns = [
    path('capabilities/', Capabilities.as_view(), name='capabilities'),
    path('is_authenticated/', is_authenticated),
    path('populate_osm/', start_osm_task)
]
