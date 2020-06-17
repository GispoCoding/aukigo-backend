import enum
from typing import Tuple

from django.contrib.gis.geos import Polygon


class GeomType(enum.Enum):
    POINT = {'postfix': 'p'}
    LINE = {'postfix': 'l'}
    POLYGON = {'postfix': 'pl'}

    @property
    def osm_model(self):
        from .models import OsmPoint, OsmLine, OsmPolygon
        if self == GeomType.POINT:
            return OsmPoint
        elif self == GeomType.LINE:
            return OsmLine
        elif self == GeomType.POLYGON:
            return OsmPolygon

    @staticmethod
    def from_feature(feature: {}):
        t = feature['geometry']['type']
        if t == 'Point':
            return GeomType.POINT
        elif t == 'LineString':
            return GeomType.LINE
        else:
            return GeomType.POLYGON


def polygon_to_overpass_bbox(geom: Polygon) -> Tuple[float, float, float, float]:
    """
    Converts GEOS polygon to bounding box understandable by Overpass API
    :param geom: GEOS Polygon
    :return: coordinates in south, west, north, east
    """
    # GEOS coordinates are in (xmin, ymin, xmax, ymax)
    geos_bbox: Tuple[float, float, float, float] = geom.extent
    return geos_bbox[1], geos_bbox[0], geos_bbox[3], geos_bbox[2]


def overpass_bbox_to_polygon(bbox: Tuple[float, float, float, float]) -> Polygon:
    """
    Converts Overpass API bounding box to GEOS polygon
    :param bbox: coordinates in south, west, north, east
    :return: Polygon
    """
    # GEOS expects coordinates in (xmin, ymin, xmax, ymax)
    geos_bbox = (bbox[1], bbox[0], bbox[3], bbox[2])
    return Polygon.from_bbox(geos_bbox)
