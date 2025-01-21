from samgeo import tms_to_geotiff
from samgeo.text_sam import LangSAM
import uuid
import json
import math
from typing import Dict, Any
from loguru import logger
import sys
import asyncio
import itertools
import os

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
    def __init__(self):
        logger.info("Initializing LangSAM model...")
        self._sam = LangSAM()
        logger.success("LangSAM model initialized successfully")

    @property
    def sam(self):
        return self._sam

    def count_tiles(self, bounding_box, zoom_level):
        """Count the number of tiles needed for the given bounding box and zoom level."""
        west, south, east, north = bounding_box
        
        def deg2num(lat, lon, zoom):
            lat_r = math.radians(lat)
            n = 2**zoom
            xtile = (lon + 180) / 360 * n
            ytile = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n
            return (xtile, ytile)
        
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
        totalnum = len(corners)
        return totalnum

    async def make_prediction(self, *, bounding_box: list, text_prompt: str, zoom_level: int = 20) -> Dict[str, Any]:
        """Make a prediction using SAM."""
        logger.info(f"Starting prediction for text_prompt='{text_prompt}', bbox={bounding_box}, zoom={zoom_level}")
        
        # Validate inputs
        if len(bounding_box) != 4:
            logger.error(f"Invalid bounding box length: {len(bounding_box)}")
            return {"error": "Bounding box must contain exactly 4 coordinates [west, south, east, north]"}
        
        # Check number of tiles
        total_tiles = self.count_tiles(bounding_box, zoom_level)
        if total_tiles > 30:  
            logger.error(f"Too many tiles requested: {total_tiles}")
            return {"error": f"Area too large for zoom level {zoom_level}. Please reduce zoom level or area size."}
        else:
            logger.info(f"Number of tiles to download: {total_tiles}")
        
        if not text_prompt.strip():
            logger.error("Empty text prompt provided")
            return {"error": "Text prompt cannot be empty"}
            
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
                async with asyncio.timeout(300):  # 5 minute timeout
                    # Run the synchronous function in a thread pool
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        tms_to_geotiff,
                        input_image,
                        bounding_box,
                        zoom_level
                    )
                logger.success("Satellite imagery downloaded successfully")
            except asyncio.TimeoutError:
                logger.error("Satellite imagery download timed out after 5 minutes")
                return {"error": "Download timed out. Please try a smaller area or lower zoom level."}
            except Exception as e:
                logger.error(f"Failed to download satellite imagery: {str(e)}", exc_info=True)
                return {"error": f"Failed to download satellite imagery: {str(e)}"}

            # Run prediction
            logger.info("Running SAM prediction...")
            try:
                # Run synchronous predict method in thread pool
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.sam.predict,
                    input_image, 
                    text_prompt, 
                    0.24,  # box_threshold 
                    0.24   # text_threshold
                )
                logger.success("SAM prediction completed successfully")
            except Exception as e:
                logger.error(f"Failed to run prediction: {str(e)}", exc_info=True)
                return {"error": f"Failed to run prediction: {str(e)}"}
            
            # Generate visualization
            logger.info("Generating visualization...")
            try:
                self.sam.show_anns(
                    cmap="Greys_r",
                    add_boxes=False,
                    alpha=1,
                    title=f"Automatic Segmentation of {text_prompt}",
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
                self.sam.tiff_to_geojson(
                    output_image,
                    output_geojson,
                    None      # simplify_tolerance
                )
                logger.success("Converted to GeoJSON successfully")
            except Exception as e:
                logger.error(f"Failed to convert to GeoJSON: {str(e)}", exc_info=True)
                return {"error": f"Failed to convert to GeoJSON: {str(e)}"}
            
            # Read GeoJSON content
            logger.info("Reading GeoJSON content...")
            try:
                with open(output_geojson, 'r') as f:
                    geojson_content = json.load(f)
                    
                if not geojson_content.get('features'):
                    logger.warning(f"No {text_prompt} found in the specified area")
                    return {"error": f"No {text_prompt} found in the specified area"}
                
                logger.success(f"Successfully found {len(geojson_content.get('features', []))} features")
                return {
                    "errors": None,
                    "version": "1.0",
                    "predictions": None,
                    "geojson": geojson_content
                }
                
            except Exception as e:
                logger.error(f"Failed to read GeoJSON output: {str(e)}", exc_info=True)
                return {"error": f"Failed to read GeoJSON output: {str(e)}"}
            
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


# Create singleton instance
predictor = SegmentationPredictor()

