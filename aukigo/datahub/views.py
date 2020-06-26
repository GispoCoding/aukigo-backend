from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import viewsets

from .models import Tileset, AreaOfInterest
from .serializers import TilesetSerializer, AreaOfInterestSerializer, OsmLayer, OsmLayerSerializer
from .tasks import load_osm_data


# ViewSets define the view behavior.
class TilesetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tileset.objects.all()
    serializer_class = TilesetSerializer


class AreaViewSet(viewsets.ModelViewSet):
    queryset = AreaOfInterest.objects.all()
    serializer_class = AreaOfInterestSerializer


class OsmLayerViewSet(viewsets.ModelViewSet):
    queryset = OsmLayer.objects.all()
    serializer_class = OsmLayerSerializer


@login_required
def start_osm_task(request):
    # Starts celery task
    load_osm_data.apply_async(queue='main')
    return JsonResponse({"status": "started!"})


def is_authenticated(request):
    return JsonResponse({"is_authenticated": request.user.is_authenticated})
