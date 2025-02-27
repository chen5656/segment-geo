from samgeo import raster_to_vector
from samgeo.text_sam import LangSAM
import uuid
import json
from typing import Dict, Any
from loguru import logger
import sys
import os
from app.config import settings 
from app.segment_geospatial.utils import transform_coordinates, download_satellite_image
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
        """Initialize the LangSAM model."""
        logger.info("Initializing LangSAM model...")
        
        try:
            logger.info(f"\n[Loading Model] model_type: {model_type}")
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
            logger.info("Cleaning up SegmentationPredictor instance")
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
        """Make a prediction using SAM."""
        logger.info("\n[Predict] Parameters:")
        logger.info(f"- bounding_box: {bounding_box}")
        logger.info(f"- text_prompt: {text_prompt}")
        logger.info(f"- box_threshold: {box_threshold} (type: {type(box_threshold)})")
        logger.info(f"- text_threshold: {text_threshold} (type: {type(text_threshold)})")
        logger.info(f"- zoom_level: {zoom_level}")

        # Generate unique filenames
        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
                
        try:
            # Download satellite imagery
            logger.info("\n[Download] Downloading satellite imagery...")
            try:
                download_satellite_image(
                    input_image,
                    bounding_box,
                    zoom_level
                )
                logger.success("[Download] Satellite imagery downloaded successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to download satellite imagery: {str(e)}")
                raise

            # Run prediction
            logger.info("\n[Predict] Running SAM prediction...")
            try:                
                self.sam.predict(
                    input_image, 
                    text_prompt, 
                    box_threshold,
                    text_threshold
                )
                logger.success("[Predict] SAM prediction completed successfully")
            except Exception:
                logger.error("[Error] Failed to run SAM prediction")
                raise
            
            # Generate visualization
            logger.info("\n[Visualize] Generating visualization...")
            try:                
                self.sam.show_anns(
                    cmap="Greys_r",
                    add_boxes=False,
                    alpha=1,
                    title=f"Automatic Segmentation of {text_prompt}",
                    blend=False,
                    output=output_image,
                )
                logger.success("[Visualize] Visualization generated successfully")
            except Exception:
                logger.error("[Error] Failed to generate visualization")
                raise

            # Convert to GeoJSON
            try:
                raster_to_vector(output_image, output_geojson, None)
                logger.success("[Convert] GeoJSON converted successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to convert to GeoJSON: No vector data found in the image")
                raise Exception("No vector data found in the image")
            
            # Read and process GeoJSON
            try:
                with open(output_geojson, 'r') as f:
                    geojson_content = json.load(f)
                logger.info(f"[Process] Loaded GeoJSON with {len(geojson_content.get('features', []))} features")
                
                transformed_geojson = transform_coordinates(geojson_content)
                geojson_count = len(transformed_geojson.get('features', []))
                logger.info(f"[Process] Transformed {geojson_count} features to WGS84")
                
                return {
                    "errors": None,
                    "version": "1.0",
                    "predictions": f"Successfully found {geojson_count} features",
                    "geojson": transformed_geojson
                }
                
            except Exception as e:
                logger.error(f"[Error] Failed to process GeoJSON: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"\n[Error] Exception occurred: {str(e)}")
            return {"error": str(e)}
            
        finally:
            # Clean up temporary files
            logger.info("\n[Cleanup] Removing temporary files...")
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        logger.info(f"[Cleanup] Removed: {file}")
                    except Exception as e:
                        logger.error(f"[Cleanup] Failed to remove {file}: {str(e)}")


# Create singleton instance
textPredictor = TextPredictor()
textPredictor.setup()