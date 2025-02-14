import os
import sys
from loguru import logger
import sys
import asyncio

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from app.predict.predict import SegmentationPredictor
from app.schemas.segmentation import SegmentationWithTextPromptRequest
from common_functions import save_geojson


class TestSegmentationPredictor:
    def __init__(self):
            self.predictor = SegmentationPredictor()
            logger.info(f"Using LangSAM model: {self.predictor.text_predictor.model_type}")

    async def test_predict_segment_with_text_prompt_success(self, request):
        
        # Run the async function
        result = await self.predictor.segment_with_text_prompt(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
            zoom_level=request.zoom_level
        )        
        
        # Validate result structure
        assert result is not None
        assert result['geojson'] is not None
        assert result['geojson']['type'] == 'FeatureCollection'
        assert len(result['geojson']['features']) > 0

        # Save the GeoJSON result
        save_geojson(
            result['geojson'], 
            f"text_detection_{request.text_prompt}_{request.zoom_level}"            
        )
        
        # Validate feature structure
        feature = result['geojson']['features'][0]
        assert feature['type'] == 'Feature'
        assert feature['geometry']['type'] == 'Polygon'
        assert len(result['geojson']['features']) == 16
        
        print(f"Found {len(result['geojson']['features'])} features")                      
        print("All assertions passed!")


if __name__ == "__main__":

    bounding_box = [-96.78806887088176,32.76760907972303,-96.78423468921088,32.769729127062774]

    request_data = {         
        "bounding_box": bounding_box,
        "text_prompt": "buildings",
        "zoom_level": 21,
        "box_threshold": 0.4,
        "text_threshold": 0.24,
    }
        
    request = SegmentationWithTextPromptRequest(**request_data)

    seg = TestSegmentationPredictor()

    asyncio.run(seg.test_predict_segment_with_text_prompt_success(request))
    