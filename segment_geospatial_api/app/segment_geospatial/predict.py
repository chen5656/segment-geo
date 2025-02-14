from samgeo import SamGeo, tms_to_geotiff, raster_to_vector
from samgeo.text_sam import LangSAM
import uuid
import json
import math
from typing import Dict, Any, List, Optional
from loguru import logger
import sys
import itertools
import os
from pyproj import Transformer
from app.config import settings
import numpy as np
from datetime import datetime

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    "segment_geospatial.log",
    rotation="500 MB",  # Rotate when file reaches 500MB
    retention="10 days",  # Keep logs for 10 days
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    backtrace=True,
    diagnose=True
)
# Also log to console
logger.add(sys.stderr, level="INFO")


class SegmentationPredictor:
    """Segmentation predictor class."""
    _instance = None
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    
    # Use settings from config
    LANGSAM_MODEL_TYPE = settings.LANGSAM_MODEL_TYPE
    SAMGEO_MODEL_TYPE = settings.SAMGEO_MODEL_TYPE
    logger.info(f"Using LangSAM model: {LANGSAM_MODEL_TYPE}")
    logger.info(f"Using SamGeo model: {SAMGEO_MODEL_TYPE}")


    def __new__(cls):
        """Create a new instance if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(SegmentationPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Empty init to maintain singleton pattern."""
        pass

    def setup(self, setup_langsam=True, setup_samgeo=True):
        """Initialize the LangSAM model.
        
        Args:
            setup_langsam (bool): Whether to set up the LangSAM model.
            setup_samgeo (bool): Whether to set up the SamGeo model.
        """
        logger.info("Setting up SegmentationPredictor...")        
        
        if setup_samgeo:
            self.setup_langsam()
        
        if setup_langsam:
            self.setup_samgeo()


    def setup_samgeo(self):
        """Set up the SamGeo model.
        
        Raises:
            RuntimeError: If model initialization fails.
        """

        # Setup SamGeo model for point prompt
        try:
            logger.info(f"Initializing SamGeo model, model_type: {self.SAMGEO_MODEL_TYPE}")
            self._samgeo = SamGeo(model_type=self.SAMGEO_MODEL_TYPE,
                                    automatic=False,
                                    sam_kwargs=None)
            logger.success("SamGeo model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SamGeo model: {str(e)}")
            raise RuntimeError(f"Failed to initialize LangSAM model: {str(e)}")

    def setup_langsam(self):
        """Set up the LangSAM model.
        
        Raises:
            RuntimeError: If model initialization fails.
        """
        # Setup LangSAM model for text prompt
        try:
            logger.info(f"Initializing LangSAM model, model_type: {self.LANGSAM_MODEL_TYPE}")
            self._langsam = LangSAM(model_type=self.LANGSAM_MODEL_TYPE)
            logger.success("LangSAM model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangSAM model: {str(e)}")
            raise RuntimeError(f"Failed to initialize LangSAM model: {str(e)}")
            
            
    @property
    def langsam(self):
        """Get the SAM model instance, initializing with default model if needed.
        
        Returns:
            LangSAM: The initialized SAM model instance.
        
        Raises:
            RuntimeError: If model initialization fails.
        """
        if not self._langsam:
            self.setup(setup_langsam=True, setup_samgeo=False)  # Initialize with default model
        return self._langsam
    
    @property
    def samgeo(self):
        """Get the SAM model instance, initializing with default model if needed.
        
        Returns:
            LangSAM: The initialized SAM model instance.
        
        Raises:
            RuntimeError: If model initialization fails.
        """
        if not self._samgeo:
            self.setup(setup_langsam=False, setup_samgeo=True)  # Initialize with default model
        return self._samgeo

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
            logger.info("Cleaning up SegmentationPredictor instance")
            self._sam = None
            self.transformer = None
            SegmentationPredictor._initialized = False

    @staticmethod
    def download_satellite_image(image_name, bounding_box, zoom_level):
        """Download a satellite image for the given bounding box and zoom level.
        
        Args:
            image_name: The name of the image to download.
            bounding_box: The bounding box to download the image for.
            zoom_level: The zoom level to download the image for.
        """
        tms_to_geotiff(
            image_name,
            bounding_box,
            zoom_level,
            source="Satellite",
            overwrite=True
        )

    async def _process_segmentation(
        self,
        type: str,
        input_image: str,
        output_image: str,
        output_geojson: str,
        points: List[List[float]] = None,
        point_labels: List[int] = None,
        text_prompt: str = None,
        box_threshold: float = 0.3,
        text_threshold: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Common processing logic for both text-based and point-based segmentation.
        
        Args:
            type: Type of segmentation to perform
            input_image: Path to input satellite image
            output_image: Path to output visualization
            output_geojson: Path to output GeoJSON
            points: Optional list of points for point-based segmentation
            point_labels: Optional list of point labels (1 for include, -1 for exclude)
            text_prompt: Optional text prompt for text-based segmentation
            box_threshold: Confidence threshold for detection
            text_threshold: Confidence threshold for text matching
            
        Returns:
            Dict containing results or error message
        """
        try:
            # Log start time
            start_time = datetime.now()
            logger.info(f"Starting segmentation at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Run prediction based on segmentation type
            if type == "input_points":
                if points is not None and point_labels is not None:                
                    # Add validation for input file path
                    if not os.path.exists(input_image):
                        raise ValueError(f"Input image file not found: {input_image}")
                
                # Ensure output paths are properly set
                if not output_image or not output_geojson:
                    raise ValueError("Output paths must be specified")
                
                self.samgeo.set_image(input_image)

                self.samgeo.predict(
                    point_coords=np.array(points),
                    point_labels=np.array(point_labels),
                    point_crs="EPSG:4326",
                    output=output_image,
                )
            elif type == "text":
                if len(text_prompt)< 3:
                    raise ValueError("Text prompt must be at least 3 characters long")
                
                logger.info(f"Running text-based prediction with prompt: '{text_prompt}'")
                self.langsam.predict(
                    input_image,
                    text_prompt,
                    box_threshold,
                    text_threshold
                )                            
                # Generate visualization for text-based segmentation
                self.langsam.show_anns(
                    cmap="Greys_r",
                    add_boxes=False,
                    alpha=1,
                    title="Segmentation Result",
                    blend=False,
                    output=output_image,
                )
            else:
                raise ValueError("No segmentation type provided")
            
            # Log completion time and duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Completed segmentation at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Segmentation processing time: {duration:.2f} seconds")
            
            # Convert to GeoJSON
            raster_to_vector(output_image, output_geojson, None)
            logger.info(f"GeoJSON converted to {output_geojson}")
            # Read and transform GeoJSON
            with open(output_geojson, 'r') as f:
                geojson_content = json.load(f)
                
            if not geojson_content.get('features'):
                return {"error": "No features found in the specified area"}
            
            transformed_geojson = self.transform_coordinates(geojson_content)
            geojson_count = len(transformed_geojson.get('features', []))
            logger.info(f"Successfully found {geojson_count} features")
            
            return {
                "errors": None,
                "version": "1.0",
                "predictions": f"Successfully found {geojson_count} features",
                "geojson": transformed_geojson
            }
            
        except Exception as e:
            logger.error(f"Error during segmentation processing: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def segment_with_points(
        self,
        zoom_level: int,
        box_threshold: float,
        points_include: List[List[float]],
        points_exclude: Optional[List[List[float]]] = None
    ) -> Dict[str, Any]:
        """
        Perform segmentation using include/exclude points.
        Automatically calculates bounding box from points.
        
        Args:
            zoom_level: Zoom level for satellite imagery
            box_threshold: Confidence threshold for detection
            points_include: List of points to include
            points_exclude: Optional list of points to exclude
            
        Returns:
            Segmentation results
        """
        # Input validation
        if not points_include:
            return {"error": "At least one include point must be provided"}
            
        if not (19 <= zoom_level <= 22):
            return {"error": "Zoom level must be between 19 and 22"}
            
        # Calculate bounding box
        buffer_size = self.calculate_buffer_size(zoom_level)
        all_points = points_include.copy()
        if points_exclude:
            all_points.extend(points_exclude)
        bounding_box = self.calculate_bounding_box(all_points, buffer_size)
        
        # Generate unique filenames
        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
        
        try:
            # Download satellite imagery
            self.download_satellite_image(input_image, bounding_box, zoom_level)
            
            # Prepare points and labels
            points = points_include + (points_exclude or [])
            point_labels = [1] * len(points_include) + [-1] * len(points_exclude or [])
            
            # Process segmentation
            result = await self._process_segmentation(
                type="input_points",
                input_image=input_image,
                output_image=output_image,
                output_geojson=output_geojson,
                points=points,
                point_labels=point_labels,
                box_threshold=box_threshold
            )
            
            return result
            
        finally:
            # Clean up temporary files
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file {file}: {str(e)}")

    async def segment_with_text_prompt(
        self,
        *,
        bounding_box: list,
        text_prompt: str,
        box_threshold: float = 0.3,
        text_threshold: float = 0.3,
        zoom_level: int = 20
    ) -> Dict[str, Any]:
        """
        Make a prediction using text prompt.
        
        Args:
            bounding_box: Coordinates [west, south, east, north]
            text_prompt: Text description of object to detect
            box_threshold: Confidence threshold for detection
            text_threshold: Confidence threshold for text matching
            zoom_level: Zoom level for satellite imagery
        """
        # Input validation
        if len(bounding_box) != 4:
            return {"error": "Bounding box must contain exactly 4 coordinates"}
            
        if not text_prompt.strip():
            return {"error": "Text prompt cannot be empty"}
            
        if not (19 <= zoom_level <= 22):
            return {"error": "Zoom level must be between 19 and 22"}
            
        # Check tile count
        total_tiles = self.count_tiles(bounding_box, zoom_level)
        if total_tiles > settings.MAX_TILES_LIMIT:
            return {
                "error": {
                    "message": f"Selected area is too large for zoom level {zoom_level}",
                    "details": {
                        "requested_tiles": total_tiles,
                        "max_tiles": settings.MAX_TILES_LIMIT
                    }
                }
            }
            
        # Generate unique filenames
        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
        
        try:
            # Download satellite imagery
            self.download_satellite_image(input_image, bounding_box, zoom_level)
            
            # Process segmentation
            result = await self._process_segmentation(
                type="text",
                input_image=input_image,
                output_image=output_image,
                output_geojson=output_geojson,
                text_prompt=text_prompt,
                box_threshold=box_threshold,
                text_threshold=text_threshold
            )
            
            return result
            
        finally:
            # Clean up temporary files
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file {file}: {str(e)}")

    @staticmethod
    def calculate_buffer_size(zoom_level: int) -> float:
        """
        Calculate buffer size in degrees based on zoom level.
        The buffer size decreases as zoom level increases.
        
        Args:
            zoom_level: Zoom level (19-22)
            
        Returns:
            Buffer size in degrees
        """
        # Base buffer size at zoom level 19
        base_buffer = 0.001
        
        # Reduce buffer size by factor of 2 for each zoom level increase
        zoom_adjustment = zoom_level - 19
        buffer_size = base_buffer / (2 ** zoom_adjustment)
        
        return buffer_size

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
predictor.setup()