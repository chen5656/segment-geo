import os
import sys
from loguru import logger
import sys
import asyncio
from datetime import datetime
import json

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from segment_geospatial_api.app.segment_geospatial.predict import predictor
from segment_geospatial_api.app.schemas.predict import PredictionRequest


def save_geojson(data, prefix="test_result"):
    """Save GeoJSON data to a file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.geojson"

    # Create results directory if it doesn't exist
    results_dir = os.path.join(project_root, "support/test_results")
    os.makedirs(results_dir, exist_ok=True)

    filepath = os.path.join(results_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"GeoJSON saved to: {filepath}")
    return filepath

class TestSegmentationPredictor:
    def __init__(self):
            self.predictor = PredictionRequest

    async def test_predict_segment_with_text_prompt_success(self, request):
        
        # Run the async function
        result = await self.predictor.make_prediction(
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
    bounding_box = [-104.99973588492506,39.753106558884284,-104.9969463875492,39.75455413892476]
    bounding_box = [-104.99973588492506,39.753106558884284,-104.9969463875492,39.75455413892476]
    bounding_box = [-76.14878853603665,43.04631460392694,-76.14757617756175,43.04701633868996]



    request_data = {         
        "bounding_box": bounding_box,
        "text_prompt": "buildings",
        "zoom_level": 22,
        "box_threshold": 0.57,
        "text_threshold": 0.55,
    }
        
    request = PredictionRequest(**request_data)

    seg = TestSegmentationPredictor()

    asyncio.run(seg.test_predict_segment_with_text_prompt_success(request))
    