import enum
import logging
import re
from typing import Tuple

from django.contrib.gis.geos import Polygon

logger = logging.getLogger(__name__)

TAG_SPLIT_PATTERN = re.compile("(?<=[a-z])[=:~]")


class GeomType(enum.Enum):
    POINT = {'postfix': 'p', 'osm_layers': ['points']}
    LINE = {'postfix': 'l', 'osm_layers': ['lines', 'multilinestrings']}
    POLYGON = {'postfix': 'pl', 'osm_layers': ['multipolygons']}

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
        elif t == 'MultiLineString':
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


def osm_tags_to_dict(tag_string: str) -> {str: str}:
    """
    Converts ogr osm tag string to tag dictionary
    :param tag_string:
    :return: tag dictionary
    """
    return dict(tag.replace('"', '').split('=>') for tag in tag_string.split('","'))


def model_tag_to_overpass_tag(tag: str) -> str:
    """
    Converts simple tags to overpass query tags
    :param tag: Tag in format key=val, key:valuefragment, key~regex, ~keyregex~regex, key=*, key
    :return: tag that can be formatted to overpass query
    """
    tag_parts = TAG_SPLIT_PATTERN.split(tag)
    sep = TAG_SPLIT_PATTERN.findall(tag)
    sep = sep[0] if len(sep) else None

    guess = f'"{tag}"'
    if len(tag_parts) == 1:  # case key (hopefully)
        pass
    elif len(tag_parts) == 2 and sep is not None:
        if tag_parts[1] == '*':
            guess = f'"{tag_parts[0]}"'
        else:
            guess = f'"{tag_parts[0]}"{sep}"{tag_parts[1]}"'
    else:
        logger.warning(f"Possibly invalid tag: '{tag}'")
    return guess
