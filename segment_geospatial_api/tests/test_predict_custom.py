import os
import sys
import glob
import json
from datetime import datetime
import unittest


# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from segment_geospatial_api.app.segment_geospatial.predict import SegmentationPredictor

from segment_geospatial_api.app.schemas.segmentation import SegmentationWithTextPromptRequest, SegmentationWithPointsRequest


class TestSegmentationPredictor:
    def __init__(self):
        self.predictor = SegmentationPredictor()
        self.predictor.setup("sam2-hiera-tiny")

    def save_geojson(data, prefix="test_result"):
        """Save GeoJSON data to a file with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.geojson"

        # Create results directory if it doesn't exist
        results_dir = os.path.join(project_root, "tests/test_results")
        os.makedirs(results_dir, exist_ok=True)

        filepath = os.path.join(results_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"GeoJSON saved to: {filepath}")
        return filepath

    async def test_predict_segment_with_text_prompt(self):
        request_data = {
            "bounding_box": [
                -96.78806887088176,
                32.76760907972303,
                -96.78423468921088,
                32.769729127062774
            ],
            "text_prompt": "buildings",
            "zoom_level": 18,
            "box_threshold": 0.4,
            "text_threshold": 0.24,
        }
            
        request = SegmentationWithTextPromptRequest(**request_data)
        
        # Run the async function
        result = await self.predictor.segment_with_text_prompt(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
        )
        
        # Validate result structure
        assert result is not None
        assert result['geojson'] is not None
        assert result['geojson']['type'] == 'FeatureCollection'
        assert len(result['geojson']['features']) > 0
        
        # Validate feature structure
        feature = result['geojson']['features'][0]
        assert feature['type'] == 'Feature'
        assert feature['geometry']['type'] == 'Polygon'
        
        # Save the GeoJSON result
        if result['geojson']:
            self.save_geojson(
                result['geojson'], 
                f"trees_detection_{request.zoom_level}"
            )
            print(f"Found {len(result['geojson']['features'])} features")
        
        # Verify temporary files are cleaned up
        temp_files = glob.glob("*.tif") + glob.glob("*.geojson")
        assert len(temp_files) == 0, f"Found temporary files that were not deleted: {temp_files}"
        
        print("All assertions passed!")

if __name__ == "__main__":
    unittest.main()
    