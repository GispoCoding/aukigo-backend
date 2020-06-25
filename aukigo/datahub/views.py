from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Layer
from .tasks import load_osm_data


class Capabilities(APIView):

    def get(self, request):
        pg_tileserv_url = "{sheme}://{host}:{port}".format(
            sheme=request.scheme,
            host=request.get_host().split(":")[0],
            port=settings.PG_TILESERV_PORT
        )

        def get_tile_url(name, is_osm):
            vector_props = "{z}/{x}/{y}.pbf"
            config_url = f"{pg_tileserv_url}/public.{name}.json"
            tileurl = f"{pg_tileserv_url}/public.{name}/{vector_props}"
            if is_osm:
                tileurl += "?properties=osmid,tags,z_order"
            return {"config": config_url, "tile": tileurl}

        layers = [{
            'name': layer.name,
            'is_osm_layer': layer.is_osm_layer,
            'tags': layer.tags,
            'urls': [get_tile_url(layer.name, False)] if not layer.is_osm_layer else [
                get_tile_url(view, True) for view in layer.views
            ]
        } for layer in Layer.objects.all()]

        capabilities = {
            'basemaps': [],
            'layers': layers
        }

        return Response(capabilities)


@login_required
def start_osm_task(request):
    # Starts celery task
    load_osm_data.apply_async(queue='main')
    return JsonResponse({"status": "started!"})


def is_authenticated(request):
    return JsonResponse({"is_authenticated": request.user.is_authenticated})
