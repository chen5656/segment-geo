from samgeo import raster_to_vector
from samgeo.text_sam import LangSAM
import uuid
import json
from typing import Dict, Any, List
from loguru import logger
import sys
import os
from app.config import settings 
from app.segment_geospatial.utils import transform_coordinates, download_satellite_image, count_tiles
from app.schemas.predict import PromptConfig

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


    def __del__(self):
        """Cleanup when instance is deleted."""
        if hasattr(self, '_sam'):
            logger.info("Cleaning up SegmentationPredictor instance")
            self._sam = None
            TextPredictor._initialized = False

    def _handle_error(self, prompt: PromptConfig, error_msg: str, results: list):
        """Helper function to handle errors consistently.
        
        Args:
            prompt (PromptConfig): The current prompt being processed
            error_msg (str): Error message to log and return
            results (list): List of results to append to
        """
        logger.error(error_msg)
        prompt_json = prompt.model_dump()
        prompt_json["type"] = "text"
        results.append({
            "prompt": prompt_json,
            "error": error_msg
        })
        return True  # Indicates should break the loop

    async def make_predictions(
        self, 
        *, 
        bounding_box: list, 
        text_prompts: List[PromptConfig],     
        zoom_level: int = 20
    ) -> Dict[str, Any]:
        """Make a prediction using SAM.
        
        Args:
            bounding_box (list): Coordinates [west, south, east, north]
            text_prompts (list):  String containing either a single word or list of words.
            box_threshold (float): Confidence threshold for object detection boxes (0-1)
            text_threshold (float): Confidence threshold for text-to-image matching (0-1)
            zoom_level (int, optional): Zoom level for satellite imagery. Defaults to 20.
        """
        logger.info(f"Starting prediction bbox={bounding_box}, zoom={zoom_level}")
        
        
        # Validate inputs
        if len(bounding_box) != 4:
            logger.error(f"Invalid bounding box length: {len(bounding_box)}")
            return {"error": "Bounding box must contain exactly 4 coordinates [west, south, east, north]"}
        
        # Check number of tiles
        total_tiles = count_tiles(bounding_box, zoom_level)
        if total_tiles > 300:  
            logger.error(f"Too many tiles requested: {total_tiles}")
            return {"error": f"Area too large for zoom level {zoom_level}. Please reduce zoom level or area size."}
        else:
            logger.info(f"Number of tiles to download: {total_tiles}")
            
        if not (1 <= zoom_level <= 22):
            logger.error(f"Invalid zoom level: {zoom_level}")
            return {"error": "Zoom level must be between 1 and 22"}

        # Generate unique filenames for this request
        request_id = str(uuid.uuid4())
        logger.info(f"Generated request ID: {request_id}")
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"

        results = []
        
        try:
            # Download satellite imagery
            logger.info("Downloading satellite imagery...")
            try:
                download_satellite_image(
                    input_image,
                    bounding_box,
                    zoom_level
                )
                logger.success("Satellite imagery downloaded successfully")
            except Exception as e:
                logger.error(f"Failed to download satellite imagery: {str(e)}", exc_info=True)
                return {"error": f"Failed to download satellite imagery: {str(e)}"}

            # Run prediction
            logger.info("Running SAM prediction...")

            for prompt in text_prompts:
                box_threshold = prompt.box_threshold
                text_threshold = prompt.text_threshold
                prompt_value = prompt.value

                # Validate thresholds
                if not (0 < box_threshold <= 1) or not (0 < text_threshold <= 1):
                    logger.error(f"Invalid threshold values: box={box_threshold}, text={text_threshold}")
                    return {"error": "Threshold values must be between 0 and 1"}
                try:
                    logger.info(f"Running SAM prediction for {prompt_value}, box_threshold={box_threshold}, text_threshold={text_threshold}")
                    self.sam.predict(
                        input_image, 
                        prompt_value, 
                        box_threshold,
                        text_threshold
                    )
                    logger.success(f"SAM prediction completed successfully")

                except Exception as e:
                    if self._handle_error(prompt, f"Failed to run prediction for {prompt}: {str(e)}", results):
                        break
                
                # Generate visualization
                logger.info("Generating visualization...")
                try:
                    self.sam.show_anns(
                        cmap="Greys_r",
                        add_boxes=False,
                        alpha=1,
                        title=f"Automatic Segmentation of {prompt_value}",
                        blend=False,
                        output=output_image,
                    )
                    logger.success("Visualization generated successfully")
                except Exception as e:
                    if self._handle_error(prompt, f"Failed to generate visualization: {str(e)}", results):
                        break
            
                # Convert to GeoJSON
                logger.info("Converting to GeoJSON...")
                try:
                    raster_to_vector(output_image, output_geojson, None)
                    logger.success("Converted to GeoJSON successfully")
                except Exception as e:
                    error_msg = f"Failed to convert to GeoJSON. There may be no {prompt_value} in the specified area"
                    if self._handle_error(prompt, error_msg, results):
                        break
            
                # Read GeoJSON content
                logger.info("Reading GeoJSON content...")
                try:
                    with open(output_geojson, 'r') as f:
                        geojson_content = json.load(f)
                        
                    if not geojson_content.get('features'):
                        error_msg = f"No {prompt_value} found in the specified area"
                        if self._handle_error(prompt, error_msg, results):
                            break
                    
                    # Transform coordinates to lat/long
                    logger.info("Transforming coordinates to WGS84...")
                    transformed_geojson = transform_coordinates(geojson_content)
                    geojson_count = len(transformed_geojson.get('features', []))
                    
                    logger.success(f"Successfully found {geojson_count} features")
                    prompt_json = prompt.model_dump()
                    prompt_json["type"] = "text"
                    results.append({
                        "prompt": prompt_json,
                        "geojson": transformed_geojson
                    })
                    
                except Exception as e:
                    if self._handle_error(prompt, f"Failed to process GeoJSON output: {str(e)}", results):
                        break
            
        finally:
            # Clean up temporary files
            logger.info("Cleaning up temporary files...")
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        logger.debug(f"Removed temporary file: {file}")
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file {file}: {str(e)}")

            # Return results
            return {
                "version": "1.0",
                "json": results                        
            }

# Create singleton instance
textPredictor = TextPredictor()
textPredictor.setup()