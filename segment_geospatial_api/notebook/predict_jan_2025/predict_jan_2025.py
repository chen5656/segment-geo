from samgeo import tms_to_geotiff, raster_to_vector
from samgeo.text_sam import LangSAM
import uuid
import json
import math
from typing import Dict, Any, List
from loguru import logger
import sys
import itertools
import os
from pyproj import Transformer
from pydantic import BaseModel, Field

class PromptConfig(BaseModel):
    value: str = Field(..., description="Text prompt for detection")
    text_threshold: float = Field(default=0.25, description="Text threshold for this specific prompt")
    box_threshold: float = Field(default=0.3, description="Box threshold for this specific prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "value": "trees",
                "text_threshold": 0.25,
                "box_threshold": 0.3
            }
        }


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
    _initialized = False
    DEFAULT_MODEL_TYPE = "sam2-hiera-large"
    
    def __new__(cls):
        """Create a new instance if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(SegmentationPredictor, cls).__new__(cls)
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
        
        Raises:
            ValueError: If invalid model_type is provided.
            RuntimeError: If model initialization fails.
        """
        logger.info("Initializing LangSAM model...")
        
        # Validate model_type
        valid_models = [
            # SAM 1 models
            "vit_h", "vit_l", "vit_b",
            # SAM 2 models
            "sam2-hiera-tiny",
            "sam2-hiera-small",
            "sam2-hiera-base-plus", 
            "sam2-hiera-large"
        ]
        if model_type not in valid_models:
            raise ValueError(
                f"Invalid model_type: {model_type}. Must be one of: {valid_models}"
            )
        
        try:
            self._sam = LangSAM(model_type=model_type)
            self.transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
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

    @staticmethod
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

    def download_satellite_image(self, image_name, bounding_box, zoom_level):
        tms_to_geotiff(
            image_name,
            bounding_box,
            zoom_level,
            source="Satellite",
            overwrite=True
        )
        
    @staticmethod
    def save_geojson(data, name):
        """Save GeoJSON data to a file with timestamp"""
        filename = f"{name}.geojson"
                
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

 
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
        total_tiles = self.count_tiles(bounding_box, zoom_level)
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
        
        try:
            # Download satellite imagery
            logger.info("Downloading satellite imagery...")
            try:
                self.download_satellite_image(
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

            results_geojson = []

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
                    # Run synchronous predict method in thread pool
                    self.sam.predict(
                        input_image, 
                        prompt_value, 
                        box_threshold,  # Use input parameter
                        text_threshold # Use input parameter
                    )
                    logger.success(f"SAM prediction completed successfully")

                except Exception as e:
                    logger.error(f"Failed to run prediction for {prompt}: {str(e)}", exc_info=True)
                    return {"error": f"Failed to run prediction for {prompt}: {str(e)}"}
                
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
                    logger.error(f"Failed to generate visualization: {str(e)}", exc_info=True)
                    return {"error": f"Failed to generate visualization: {str(e)}"}
            
                # Convert to GeoJSON
                logger.info("Converting to GeoJSON...")
                try:
                    raster_to_vector(output_image, output_geojson, None)
                    logger.success("Converted to GeoJSON successfully")
                except Exception as e:
                    logger.error(f"Failed to convert to GeoJSON: {str(e)}. There may be no {prompt_value} in the specified area", exc_info=True)
                    return {"error": f"Failed to convert to GeoJSON: {str(e)}. There may be no {prompt_value} in the specified area"}
            
                # Read GeoJSON content
                logger.info("Reading GeoJSON content...")
                try:
                    with open(output_geojson, 'r') as f:
                        geojson_content = json.load(f)
                        
                    if not geojson_content.get('features'):
                        logger.warning(f"No {prompt_value} found in the specified area")
                        return {"error": f"No {prompt_value} found in the specified area"}
                    
                    # Transform coordinates to lat/long
                    logger.info("Transforming coordinates to WGS84...")
                    transformed_geojson = self.transform_coordinates(geojson_content)
                    geojson_count = len(transformed_geojson.get('features', []))
                    
                    logger.success(f"Successfully found {geojson_count} features")
                    results_geojson.append(transformed_geojson)
                    
                except Exception as e:
                    logger.error(f"Failed to process GeoJSON output: {str(e)}", exc_info=True)
                    return {"error": f"Failed to process GeoJSON output: {str(e)}"}
            
            return {
                        "errors": None,
                        "version": "1.0",
                        "predictions": "",
                        "geojson": results_geojson
                    }
            
        finally:
            # Clean up temporary files
            logger.info("Cleaning up temporary files...")
            # for file in [input_image, output_image, output_geojson]:
            #     if os.path.exists(file):
            #         try:
            #             os.remove(file)
            #             logger.debug(f"Removed temporary file: {file}")
            #         except Exception as e:
            #             logger.warning(f"Failed to remove temporary file {file}: {str(e)}")


# Create singleton instance
predictor = SegmentationPredictor()
predictor.setup()