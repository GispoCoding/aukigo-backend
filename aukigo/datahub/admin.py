from django.contrib.gis import admin
from .models import Layer, AreaOfInterest


class OsmAdmin(admin.GeoModelAdmin):
    default_lat = 65
    default_lon = 25
    default_zoom = 6


# Register your models here.
admin.site.register(AreaOfInterest, OsmAdmin)
admin.site.register(Layer)
