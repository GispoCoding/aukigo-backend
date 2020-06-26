from django.contrib.gis import admin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from .models import OsmLayer, AreaOfInterest


class OsmAdmin(admin.GeoModelAdmin):
    default_lat = 65
    default_lon = 25
    default_zoom = 6


class ArrayAdmin(admin.ModelAdmin, DynamicArrayMixin):
    pass


# Register your models here.
admin.site.register(AreaOfInterest, OsmAdmin)
admin.site.register(OsmLayer, ArrayAdmin)
