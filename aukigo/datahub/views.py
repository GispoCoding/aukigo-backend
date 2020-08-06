from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tileset, AreaOfInterest, WMTSBasemap, VectorTileBasemap, Layer
from .serializers import (TilesetSerializer, AreaOfInterestSerializer, OsmLayer, OsmLayerSerializer,
                          WTMSBasemapSerializer, VectorTileBasemapSerializer, LayerSerializer, OsmPointSerializer,
                          OsmPolygonSerializer, OsmLineSerializer)
from .tasks import load_osm_data

# ViewSets define the view behavior.
from .utils import GeomType


class TilesetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tileset.objects.all()
    serializer_class = TilesetSerializer


class LayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer


class AreaViewSet(viewsets.ModelViewSet):
    queryset = AreaOfInterest.objects.all()
    serializer_class = AreaOfInterestSerializer


class OsmLayerViewSet(viewsets.ModelViewSet):
    queryset = OsmLayer.objects.all()
    serializer_class = OsmLayerSerializer


class WMTSBasemapViewSet(viewsets.ModelViewSet):
    queryset = WMTSBasemap.objects.all()
    serializer_class = WTMSBasemapSerializer


class VectorTileBasemapViewSet(viewsets.ModelViewSet):
    queryset = VectorTileBasemap.objects.all()
    serializer_class = VectorTileBasemapSerializer


class Capabilities(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        def serialize_all(view_set: viewsets.ModelViewSet) -> list:
            return view_set.as_view({'get': 'list'})(request._request).data

        data = {
            'basemaps': {
                'WMTS': serialize_all(WMTSBasemapViewSet),
                'vectorTile': serialize_all(VectorTileBasemapViewSet)
            },
            'tilesets': serialize_all(LayerViewSet)
        }

        return Response(data)


class OsmGeojsons(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, layer, gtype):
        gtype = GeomType[gtype]
        layer = Layer.objects.get(pk=layer)
        objects = layer.osm_layer.get_objects_for_type(gtype)

        if gtype == GeomType.POINT:
            serializer_class = OsmPointSerializer
        elif gtype == GeomType.LINE:
            serializer_class = OsmLineSerializer
        else:
            serializer_class = OsmPolygonSerializer
        serializer = serializer_class(objects, many=True)
        return JsonResponse(serializer.data, safe=False)


@login_required
def start_osm_task(request):
    # Starts celery task
    load_osm_data.apply_async(queue='main')
    return JsonResponse({"status": "started!"})


def is_authenticated(request):
    return JsonResponse({"is_authenticated": request.user.is_authenticated})
