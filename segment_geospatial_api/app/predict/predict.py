import os
import uuid
import json
import math
from typing import List, Tuple, Dict, Any
import itertools
import numpy as np
from samgeo import raster_to_vector
from .textPredictor import TextSegmentationPredictor
from .pointPredictor import PointSegmentationPredictor
from .basePredictor import logger
from app.config import settings
from fastapi import HTTPException


def singleton(cls):
    """Singleton decorator"""
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

class ValidationError(HTTPException):
    """Custom validation error that matches frontend error handling"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            status_code=400,
            detail={
                "message": message,
                "details": details or {}
            }
        )

@singleton
class SegmentationPredictor:
    """Facade for all segmentation operations"""
    
    MAX_TILES_LIMIT = settings.MAX_TILES_LIMIT  
    MIN_ZOOM_LEVEL = settings.MIN_ZOOM_LEVEL
    MAX_ZOOM_LEVEL = settings.MAX_ZOOM_LEVEL
    BUFFER_SIZE_DEGREES = settings.BUFFER_DEGREES_FOR_POINT_PREDICTION

    def __init__(self):
        self.text_predictor = TextSegmentationPredictor()
        self.point_predictor = PointSegmentationPredictor()

    def validate_zoom_level(self, zoom_level: int) -> None:
        """Validate zoom level is within acceptable range."""
        if not self.MIN_ZOOM_LEVEL <= zoom_level <= self.MAX_ZOOM_LEVEL:
            raise ValidationError(
                message=f"Zoom level must be between {self.MIN_ZOOM_LEVEL} and {self.MAX_ZOOM_LEVEL}",
                details={
                    "zoom_level": zoom_level,
                    "min_zoom": self.MIN_ZOOM_LEVEL,
                    "max_zoom": self.MAX_ZOOM_LEVEL
                }
            )

    def validate_bounding_box_size(self, bounding_box: List[float], zoom_level: int) -> None:
        """Validate bounding box size and tile count."""
        # Validate bounding box format
        if len(bounding_box) != 4:
            raise ValidationError(
                message="Invalid bounding box format",
                details={
                    "expected": "4 coordinates [west, south, east, north]",
                    "received": len(bounding_box)
                }
            )

        west, south, east, north = bounding_box

        # Validate coordinate ranges
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValidationError(
                message="Invalid longitude values",
                details={
                    "west": west,
                    "east": east,
                    "valid_range": "[-180, 180]"
                }
            )
        
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValidationError(
                message="Invalid latitude values",
                details={
                    "south": south,
                    "north": north,
                    "valid_range": "[-90, 90]"
                }
            )

        # Check tile count
        tile_count = self.count_tiles(bounding_box, zoom_level)
        if tile_count > self.MAX_TILES_LIMIT:
            raise ValidationError(
                message="Area too large",
                details={
                    "tiles_required": tile_count,
                    "max_tiles": self.MAX_TILES_LIMIT,
                    "suggestion": "Try reducing the area or zoom level"
                }
            )

    async def segment_with_text_prompt(self, *, bounding_box, text_prompt, box_threshold=0.3, text_threshold=0.3, zoom_level=20):
        """Make a prediction using text prompt"""
        # Validate inputs
        self.validate_zoom_level(zoom_level)
        self.validate_bounding_box_size(bounding_box, zoom_level)
        
        if not text_prompt or len(text_prompt.strip()) == 0:
            raise ValidationError(
                message="Text prompt cannot be empty",
                details={
                    "text_prompt": text_prompt
                }
            )

        if not (0 <= box_threshold <= 1 and 0 <= text_threshold <= 1):
            raise ValidationError(
                message="Threshold values must be between 0 and 1",
                details={
                    "box_threshold": box_threshold,
                    "text_threshold": text_threshold
                }
            )

        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"

        try:
            self.text_predictor.download_satellite_image(input_image, bounding_box, zoom_level)
            await self.text_predictor.predict(input_image, text_prompt, box_threshold, text_threshold, output_image)
            
            # Convert to GeoJSON
            raster_to_vector(output_image, output_geojson, None)
            
            with open(output_geojson, 'r') as f:
                geojson_content = json.load(f)
                
            transformed_geojson = self.text_predictor.transform_coordinates(geojson_content)

            logger.info(f"Found {len(transformed_geojson['features'])} features")
            
            return {
                "errors": None,
                "version": "1.0",
                "predictions": f"Successfully processed",
                "geojson": transformed_geojson
            }
        finally:
            # Clean up temporary files
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    os.remove(file)

    async def segment_with_points(self, zoom_level, box_threshold, points_include, points_exclude=None):
        """Perform segmentation using include/exclude points"""
        logger.info("Starting point segmentation:")
        
        # Validate inputs
        self.validate_zoom_level(zoom_level)
        
        if not points_include or len(points_include) == 0:
            raise ValidationError(
                message="At least one include point is required",
                details={
                    "points_include": points_include
                }
            )

        if not (0 <= box_threshold <= 1):
            raise ValidationError(
                message="Box threshold must be between 0 and 1",
                details={
                    "box_threshold": box_threshold
                }
            )

        # Calculate and validate bounding box
        buffer_size = self.calculate_buffer_size(zoom_level)
        
        all_points = points_include + (points_exclude or [])
        
        bounding_box = self.calculate_bounding_box(all_points, buffer_size)
        logger.info(f"Calculated bounding box: {bounding_box}")
        self.validate_bounding_box_size(bounding_box, zoom_level)

        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"

        try:
            point_labels = [1] * len(points_include) + [-1] * len(points_exclude or [])
            self.point_predictor.download_satellite_image(input_image, bounding_box, zoom_level)
            
            await self.point_predictor.predict(input_image, points_include + (points_exclude or []), point_labels, box_threshold, output_image)
            
            # Convert to GeoJSON
            raster_to_vector(output_image, output_geojson, None)
            
            with open(output_geojson, 'r') as f:
                geojson_content = json.load(f)
                
            transformed_geojson = self.point_predictor.transform_coordinates(geojson_content)
            
            logger.info(f"Found {len(transformed_geojson['features'])} features")
            
            return {
                "errors": None,
                "version": "1.0",
                "predictions": f"Successfully processed",
                "geojson": transformed_geojson
            }
        finally:
            # Clean up temporary files
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    os.remove(file)

    @staticmethod
    def count_tiles(bounding_box, zoom_level):
        """Count the number of tiles needed for the given bounding box and zoom level.
        
        Args:
            bounding_box: The bounding box to count tiles for.
            zoom_level: The zoom level to count tiles for.
            
        Returns:
            The number of tiles needed for the given bounding box and zoom level.
        """
        def deg2num(lat, lon, zoom):
            lat_r = math.radians(lat)
            n = 2**zoom
            x_tile = (lon + 180) / 360 * n
            y_tile = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n
            return x_tile, y_tile

        # Convert bounding box coordinates to tile coordinates
        west, south, east, north = bounding_box
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

    def transform_coordinates(self, geojson_data):
        """Transform coordinates from EPSG:3857 to EPSG:4326
        
        Args:
            geojson_data: The GeoJSON data to transform.
            
        Returns:
            The transformed GeoJSON data.
        """
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

        # Update CRS to WGS84
        geojson_data['crs'] = {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::4326"
            }
        }
        return geojson_data

    def __del__(self):
        """Cleanup when instance is deleted."""
        if hasattr(self, '_sam'):
            logger.success("Cleaning up SegmentationPredictor instance")
            self._sam = None
            self.transformer = None
            SegmentationPredictor._initialized = False

    
    def calculate_buffer_size(self, zoom_level: int) -> float:
        """
        Calculate buffer size in degrees based on zoom level.
        
        Args:
            zoom_level: Zoom level (19-22)
            
        Returns:
            Buffer size in degrees
        """
        return self.BUFFER_SIZE_DEGREES  # 直接返回固定值，不再根据zoom level调整

    @staticmethod
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


# Create singleton instance
predictor = SegmentationPredictor()
