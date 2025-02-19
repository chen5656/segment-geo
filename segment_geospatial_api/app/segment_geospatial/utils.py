import math
import itertools    
from pyproj import Transformer  
from samgeo import tms_to_geotiff
import numpy as np
from typing import List

def count_tiles(bounding_box, zoom_level):
    """Count the number of tiles needed for the given bounding box and zoom level."""
    west, south, east, north = bounding_box

    def deg2num(lat, lon, zoom):
        lat_r = math.radians(lat)
        n = 2**zoom
        xtile = (lon + 180) / 360 * n
        ytile = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n
        return xtile, ytile

    # Convert bounding box coordinates to tile coordinates
    x0, y0 = deg2num(south, west, zoom_level)
    x1, y1 = deg2num(north, east, zoom_level)

    x0, x1 = sorted([x0, x1])
    y0, y1 = sorted([y0, y1])
    corners = tuple(
        itertools.product(
            range(math.floor(x0), math.ceil(x1)),
            range(math.floor(y0), math.ceil(y1)),
        )
    )
    total_num = len(corners)
    return total_num


def transform_coordinates(geojson_data):
    """Transform coordinates from EPSG:3857 to EPSG:4326"""
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    if not geojson_data or 'features' not in geojson_data:
        return geojson_data

    for feature in geojson_data['features']:
        if 'geometry' not in feature:
            continue

        geometry = feature['geometry']
        if geometry['type'] == 'Polygon':
            for i, ring in enumerate(geometry['coordinates']):
                transformed_coords = []
                for x, y in ring:
                    lon, lat = transformer.transform(x, y)
                    transformed_coords.append([lon, lat])
                geometry['coordinates'][i] = transformed_coords
        elif geometry['type'] == 'MultiPolygon':
            for i, polygon in enumerate(geometry['coordinates']):
                for j, ring in enumerate(polygon):
                    transformed_coords = []
                    for x, y in ring:
                        lon, lat = transformer.transform(x, y)
                        transformed_coords.append([lon, lat])
                    geometry['coordinates'][i][j] = transformed_coords
    return geojson_data

def download_satellite_image(image_name, bounding_box, zoom_level):
    tms_to_geotiff(
        image_name,
        bounding_box,
        zoom_level,
        source="Satellite",
        overwrite=True
    )

def calculate_bounding_box(points: List[List[float]], buffer_size: float) -> List[float]:
    """
    Calculate bounding box from points with buffer.
    
    Args:
        points: List of [longitude, latitude] coordinates
        buffer_size: Buffer size in degrees
        
    Returns:
        [min_lon, min_lat, max_lon, max_lat]
    """

    points_array = np.array(points)
    min_lon = points_array[:, 0].min() - buffer_size
    min_lat = points_array[:, 1].min() - buffer_size
    max_lon = points_array[:, 0].max() + buffer_size
    max_lat = points_array[:, 1].max() + buffer_size
    
    return [min_lon, min_lat, max_lon, max_lat]
    