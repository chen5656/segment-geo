import os
import sys
import asyncio
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from app.segment_geospatial.predict import predictor
from app.schemas.predict import PredictionRequest
from common_functions import save_geojson

class TestSegmentationPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = predictor
        bounding_box = [-76.14878853603665,43.04631460392694,-76.14757617756175,43.04701633868996]
        request_data = {
            "bounding_box": bounding_box,
            "text_prompt": "buildings",
            "zoom_level": 20,
            "box_threshold": 0.4,
            "text_threshold": 0.24,
        }
        self.request = PredictionRequest(**request_data)

    def test_text_predict_segment_success(self):
     
        request = self.request
        # Run the async function
        result = asyncio.run(self.predictor.make_prediction(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
            zoom_level=request.zoom_level
        ))       
        
        # Validate result structure
        self.assertIsNotNone(result, "Result should not be None")
        self.assertIsNotNone(result['geojson'], "GeoJSON should not be None")


        # Save the GeoJSON result
        save_geojson(
            result['geojson'], 
            f"text_detection_{request.text_prompt}_{request.zoom_level}"            
        )
        
        self.assertEqual(result['geojson']['type'], 'FeatureCollection', "Type should be FeatureCollection")
        self.assertGreater(len(result['geojson']['features']), 0, "Should have at least one feature")
        self.assertEqual(len(result['geojson']['features']), 4, "Should be 4 features")


if __name__ == "__main__":
    unittest.main()
    