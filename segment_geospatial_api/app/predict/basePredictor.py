from pyproj import Transformer
from loguru import logger
from samgeo import tms_to_geotiff
import sys

# Configure loguru logger
logger.remove()
logger.add(
    "support/segment_geospatial.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,
    diagnose=True
)
logger.add(sys.stderr, level="INFO")

class BasePredictor:
    """Base predictor with common functionality"""
    def __init__(self):
        self.transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    def transform_coordinates(self, geojson_data):
        """Transform coordinates from EPSG:3857 to EPSG:4326"""
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
                        lon, lat = self.transformer.transform(x, y)
                        transformed_coords.append([lon, lat])
                    geometry['coordinates'][i] = transformed_coords
            elif geometry['type'] == 'MultiPolygon':
                for i, polygon in enumerate(geometry['coordinates']):
                    for j, ring in enumerate(polygon):
                        transformed_coords = []
                        for x, y in ring:
                            lon, lat = self.transformer.transform(x, y)
                            transformed_coords.append([lon, lat])
                        geometry['coordinates'][i][j] = transformed_coords

        geojson_data['crs'] = {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::4326"
            }
        }
        return geojson_data

    @staticmethod
    def download_satellite_image(image_name, bounding_box, zoom_level):
        """Download satellite image for the given bounding box and zoom level"""        
        tms_to_geotiff(
            output=image_name,
            bbox=bounding_box,
            zoom=zoom_level,
            source="Satellite",
            overwrite=True
        )
