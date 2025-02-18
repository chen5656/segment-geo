from samgeo import tms_to_geotiff, raster_to_geojson, raster_to_vector
from samgeo.text_sam import LangSAM
import uuid
import json
import math
from typing import Dict, Any
from loguru import logger
import sys
import itertools
import os
from pyproj import Transformer
from app.config import settings
import inspect

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
    DEFAULT_MODEL_TYPE = settings.DEFAULT_MODEL_TYPE
    
    def __new__(cls):
        """Create a new instance if one doesn't exist."""
        if cls._instance is None:
            cls._instance = super(SegmentationPredictor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Empty init to maintain singleton pattern."""
        pass

    def setup(self, model_type=DEFAULT_MODEL_TYPE):
        """Initialize the LangSAM model."""
        logger.info("Initializing LangSAM model...")
        print(f"\n[Setup] model_type: {model_type}")
        
        try:
            print(f"\n[Loading Model] model_type: {model_type}")
            self._sam = LangSAM(model_type=model_type)
            print(f"[Model Loaded] Model attributes: {dir(self._sam)}")
            print(f"[Model Loaded] Model type: {type(self._sam)}")
            
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
        print("\n[Predict] Parameters:")
        print(f"- bounding_box: {bounding_box}")
        print(f"- text_prompt: {text_prompt}")
        print(f"- box_threshold: {box_threshold} (type: {type(box_threshold)})")
        print(f"- text_threshold: {text_threshold} (type: {type(text_threshold)})")
        print(f"- zoom_level: {zoom_level}")

        # Generate unique filenames
        request_id = str(uuid.uuid4())
        input_image = f"satellite_{request_id}.tif"
        output_image = f"segment_{request_id}.tif"
        output_geojson = f"segment_{request_id}.geojson"
        
        print(f"\n[Files] Generated filenames:")
        print(f"- input_image: {input_image}")
        print(f"- output_image: {output_image}")
        print(f"- output_geojson: {output_geojson}")
        
        try:
            # Download satellite imagery
            print("\n[Download] Downloading satellite imagery...")
            try:
                self.download_satellite_image(
                    input_image,
                    bounding_box,
                    zoom_level
                )
                print("[Download] Satellite imagery downloaded successfully")
            except Exception as e:
                print(f"[Error] Failed to download satellite imagery: {str(e)}")
                raise

            # Run prediction
            print("\n[Predict] Running SAM prediction...")
            try:
                # 打印predict方法的签名
                predict_signature = inspect.signature(self.sam.predict)
                print(f"[Method Signature] predict: {predict_signature}")
                
                self.sam.predict(
                    input_image, 
                    text_prompt, 
                    box_threshold,
                    text_threshold
                )
                print("[Predict] SAM prediction completed successfully")
            except Exception as e:
                print(f"[Error] Failed to run prediction: {str(e)}")
                print(f"[Error] Exception type: {type(e)}")
                raise
            
            # Generate visualization
            print("\n[Visualize] Generating visualization...")
            try:
                # 打印show_anns方法的签名
                show_anns_signature = inspect.signature(self.sam.show_anns)
                print(f"[Method Signature] show_anns: {show_anns_signature}")
                
                self.sam.show_anns(
                    cmap="Greys_r",
                    add_boxes=False,
                    alpha=1,
                    title=f"Automatic Segmentation of {text_prompt}",
                    blend=False,
                    output=output_image,
                )
                print("[Visualize] Visualization completed")
            except Exception as e:
                print(f"[Error] Failed to generate visualization: {str(e)}")
                raise
            
            # Convert to GeoJSON
            print("\n[Convert] Converting to GeoJSON...")
            try:
                raster_to_vector(output_image, output_geojson, None)
                print("[Convert] Converted to GeoJSON successfully")
            except Exception as e:
                print(f"[Error] Failed to convert to GeoJSON: {str(e)}")
                raise
            
            # Read and process GeoJSON
            print("\n[Process] Processing GeoJSON...")
            try:
                with open(output_geojson, 'r') as f:
                    geojson_content = json.load(f)
                print(f"[Process] Loaded GeoJSON with {len(geojson_content.get('features', []))} features")
                
                transformed_geojson = self.transform_coordinates(geojson_content)
                geojson_count = len(transformed_geojson.get('features', []))
                print(f"[Process] Transformed {geojson_count} features to WGS84")
                
                return {
                    "errors": None,
                    "version": "1.0",
                    "predictions": f"Successfully found {geojson_count} features",
                    "geojson": transformed_geojson
                }
                
            except Exception as e:
                print(f"[Error] Failed to process GeoJSON: {str(e)}")
                raise
            
        except Exception as e:
            print(f"\n[Error] Exception occurred: {str(e)}")
            print(f"[Error] Exception type: {type(e)}")
            return {"error": str(e)}
            
        finally:
            # Clean up temporary files
            print("\n[Cleanup] Removing temporary files...")
            for file in [input_image, output_image, output_geojson]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                        print(f"[Cleanup] Removed: {file}")
                    except Exception as e:
                        print(f"[Cleanup] Failed to remove {file}: {str(e)}")


# Create singleton instance
predictor = SegmentationPredictor()
predictor.setup()