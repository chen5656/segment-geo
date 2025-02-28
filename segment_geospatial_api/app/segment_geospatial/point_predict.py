from samgeo import raster_to_vector, SamGeo
import uuid
import json
from typing import Dict, Any
from loguru import logger
import sys
import os
from pyproj import Transformer
from app.config import settings
import numpy as np
from app.segment_geospatial.utils import transform_coordinates, download_satellite_image, calculate_bounding_box
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


class PointPredictor:
    """Segmentation predictor class that supports both text and point-based prediction."""
    _instance = None
    _initialized = False
    DEFAULT_MODEL_TYPE = settings.DEFAULT_POINT_MODEL_TYPE  # Add point model type
    DEFAULT_BUFFER_SIZE = settings.BUFFER_DEGREES_FOR_POINT_PREDICTION
    
    def __new__(cls):
        """Create a new instance if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(PointPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Empty init to maintain singleton pattern."""
        pass

    def setup(self, model_type=DEFAULT_MODEL_TYPE):
        """Initialize both LangSAM and SamGeo models."""
        logger.info("Initializing models...")
        
        try:            
            # Initialize point-based model
            logger.info(f"\n[Loading Point Model] model_type: {self.DEFAULT_MODEL_TYPE}")
            self._sam = SamGeo(
                model_type=model_type,
                automatic=False,
                sam_kwargs=None
            )
            
            self.transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
            self._initialized = True
            logger.success("Models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            raise RuntimeError(f"Failed to initialize models: {str(e)}")

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
            self.transformer = None
            PointPredictor._initialized = False

    async def make_prediction(
        self,
        *,
        points_include: list,
        points_exclude: list = None,
        box_threshold: float = 0.3,
        zoom_level: int = 20
    ) -> Dict[str, Any]:
        """Make a prediction using points."""
        logger.info("\n[Point Predict] Parameters:")
        logger.info(f"- points_include: {points_include}")
        logger.info(f"- points_exclude: {points_exclude}")
        logger.info(f"- box_threshold: {box_threshold}")
        logger.info(f"- zoom_level: {zoom_level}")

        # Generate unique filenames
        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
        
        all_points = points_include + (points_exclude or [])
        
        bounding_box = calculate_bounding_box(all_points, self.DEFAULT_BUFFER_SIZE)

        results = []
        prompt_json = None
                
        try:
            prompt_json = {
                "points_include": points_include,
                "points_exclude": points_exclude,
                "box_threshold": box_threshold,
                "zoom_level": zoom_level,
                "type": "points"
            }

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

            # Run point-based prediction
            logger.info("\n[Predict] Running point-based prediction...")
            try:
                all_points = points_include + (points_exclude or [])
                point_labels = [1] * len(points_include) + [-1] * len(points_exclude or [])
                
                self.sam.set_image(input_image)
                self.sam.predict(
                    point_coords=np.array(all_points),
                    point_labels=np.array(point_labels),
                    point_crs="EPSG:4326",
                    box_threshold=box_threshold,
                    output=output_image
                )
                logger.success("[Predict] Point-based prediction completed successfully")
            except Exception as e:
                logger.error(f"[Error] Failed to run point-based prediction: {str(e)}")
                raise

            # Convert to GeoJSON and process
            try:
                raster_to_vector(output_image, output_geojson, None)
                logger.success("[Convert] GeoJSON converted successfully")
                
                with open(output_geojson, 'r') as f:
                    geojson_content = json.load(f)
                logger.info(f"[Process] Loaded GeoJSON with {len(geojson_content.get('features', []))} features")
                
                transformed_geojson = transform_coordinates(geojson_content)
                geojson_count = len(transformed_geojson.get('features', []))
                logger.info(f"[Process] Transformed {geojson_count} features to WGS84")

                results.append({
                    "prompt": prompt_json,
                    "geojson": transformed_geojson
                })          
            except Exception as e:
                logger.error(f"[Error] Failed to process GeoJSON: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"\n[Error] Exception occurred: {str(e)}")
            results.append({
                "prompt": prompt_json,
                "error": f"\n[Error] Exception occurred: {str(e)}"
            })
            
        finally:
            # Return results
            return {
                    "version": "1.0",
                    "json": results                        
            }    
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
pointPredictor = PointPredictor()
pointPredictor.setup()