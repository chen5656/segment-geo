from samgeo import raster_to_vector
from samgeo.text_sam import LangSAM
import uuid
import json
from typing import Dict, Any
from loguru import logger
import sys
import os
from app.config import settings
from app.segment_geospatial.utils import transform_coordinates, download_satellite_image, count_tiles

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


class TextPredictor:
    """Segmentation predictor class."""
    _instance = None
    _initialized = False
    DEFAULT_MODEL_TYPE = settings.DEFAULT_TEXT_MODEL_TYPE
    
    def __new__(cls):
        """Create a new instance if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(TextPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Empty init to maintain singleton pattern."""
        pass

    def setup(self, model_type=DEFAULT_MODEL_TYPE):
        """Initialize the LangSAM model.
        
        Args:
            model_type (str): The model type to use. Can be one of:
                SAM 1 models:
                - "vit_h"
                - "vit_l"
                - "vit_b"
                SAM 2 models:
                - "sam2-hiera-tiny"
                - "sam2-hiera-small" 
                - "sam2-hiera-base-plus"
                - "sam2-hiera-large" (default)
        """
        logger.info("Initializing LangSAM model...")
        
        try:
            self._sam = LangSAM(model_type=model_type)

            self._initialized = True
            logger.success("LangSAM model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangSAM model: {str(e)}")
            raise RuntimeError(f"Failed to initialize LangSAM model: {str(e)}")

    @property
    def sam(self):
        """Get the SAM model instance, initializing with default model if needed.
        
        Returns:
            LangSAM: The initialized SAM model instance.
        
        Raises:
            RuntimeError: If model initialization fails.
        """
        if not self._initialized:
            self.setup()  # Initialize with default model
        return self._sam


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
            logger.info("Cleaning up TextPredictor instance")
            self._sam = None
            TextPredictor._initialized = False


    async def make_prediction(
        self, 
        *, 
        bounding_box: list, 
        text_prompt: str, 
        box_threshold: float = 0.3,
        text_threshold: float = 0.3,
        zoom_level: int = 20
    ) -> Dict[str, Any]:
        """Make a prediction using SAM.
        
        Args:
            bounding_box (list): Coordinates [west, south, east, north]
            text_prompt (str): Text description of object to detect
            box_threshold (float): Confidence threshold for object detection boxes (0-1)
            text_threshold (float): Confidence threshold for text-to-image matching (0-1)
            zoom_level (int, optional): Zoom level for satellite imagery. Defaults to 20.
        """
        logger.info(
            f"Starting prediction for text_prompt='{text_prompt}', "
            f"bbox={bounding_box}, zoom={zoom_level}, "
            f"box_threshold={box_threshold}, text_threshold={text_threshold}"
        )
        # Validate thresholds
        if not (0 < box_threshold <= 1) or not (0 < text_threshold <= 1):
            logger.error(f"[Error] Invalid threshold values: box={box_threshold}, text={text_threshold}")
            return {"error": "Threshold values must be between 0 and 1"}
        
        # Validate inputs
        if len(bounding_box) != 4:
            logger.error(f"[Error] Invalid bounding box length: {len(bounding_box)}")
            return {"error": "Bounding box must contain exactly 4 coordinates [west, south, east, north]"}
        
        # Check number of tiles
        total_tiles = count_tiles(bounding_box, zoom_level)
        if total_tiles > settings.MAX_TILES_LIMIT:  
            logger.error(f"[Error] Too many tiles requested: {total_tiles}, maximum allowed tiles: {settings.MAX_TILES_LIMIT}")
            return {"error": f"Selected area is too large for zoom level {zoom_level}, maximum allowed tiles: {settings.MAX_TILES_LIMIT}, requested tiles: {total_tiles}"}
        else:
            logger.info(f"[Info] Number of tiles to download: {total_tiles}")
        
        if not text_prompt.strip():
            logger.error("Empty text prompt provided")
            return {"error": "Text prompt cannot be empty"}
            
        if not (1 <= zoom_level <= 22):
            logger.error(f"Invalid zoom level: {zoom_level}")
            return {"error": "Zoom level must be between 1 and 22"}

        # Generate unique filenames for this request
        request_id = str(uuid.uuid4())
        logger.info(f"[Info] Generated request ID: {request_id}")
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
        
        try:
            # Download satellite imagery
            logger.info("[Info] Downloading satellite imagery...")
            try:
                download_satellite_image(
                    input_image,
                    bounding_box,
                    zoom_level
                )
                logger.success("[Info] Satellite imagery downloaded successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to download satellite imagery: {str(e)}", exc_info=True)
                return {"error": f"Failed to download satellite imagery: {str(e)}"}

            # Run prediction
            logger.info("[Info] Running SAM prediction...")
            try:
                self.sam.predict(
                    input_image, 
                    text_prompt, 
                    box_threshold,
                    text_threshold
                )
                logger.success("[Info] SAM prediction completed successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to run prediction: {str(e)}", exc_info=True)
                return {"error": f"Failed to run prediction: {str(e)}"}
            
            # Generate visualization
            logger.info("[Info] Generating visualization...")
            try:
                self.sam.show_anns(
                    cmap="Greys_r",
                    add_boxes=False,
                    alpha=1,
                    title=f"Automatic Segmentation of {text_prompt}",
                    blend=False,
                    output=output_image,
                )
                logger.success("[Info] Visualization generated successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to generate visualization: {str(e)}", exc_info=True)
                return {"error": f"Failed to generate visualization: {str(e)}"}
            
            # Convert to GeoJSON
            logger.info("[Info] Converting to GeoJSON...")
            try:
                raster_to_vector(output_image, output_geojson, None)
                logger.success("[Info] Converted to GeoJSON successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to convert to GeoJSON: {str(e)}. There may be no {text_prompt} in the specified area", exc_info=True)
                return {"error": f"Failed to convert to GeoJSON: {str(e)}. There may be no {text_prompt} in the specified area"}
            
            # Read GeoJSON content
            logger.info("[Info] Reading GeoJSON content...")
            with open(output_geojson, 'r') as f:
                geojson_content = json.load(f)
                
   
            # Transform coordinates to lat/long
            logger.info("[Info] Transforming coordinates to WGS84...")
            transformed_geojson = transform_coordinates(geojson_content)
            geojson_count = len(transformed_geojson.get('features', []))
            
            logger.success(f"Successfully found {geojson_count} features")
            return {
                "errors": None,
                "version": "1.0",
                "predictions": f"Successfully found {geojson_count} features",
                "geojson": transformed_geojson
            }
                   
        finally:
            # Clean up temporary files
            logger.info("[Info] Cleaning up temporary files...")
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        logger.debug(f"[Info] Removed temporary file: {file}")
                    except Exception as e:
                        logger.warning(f"[Warning] Failed to remove temporary file {file}: {str(e)}")


# Create singleton instance
predictor = TextPredictor()
predictor.setup()