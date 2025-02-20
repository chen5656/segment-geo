import os
import sys
import asyncio
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from app.segment_geospatial.point_predict import pointPredictor
from app.schemas.predict import PointPredictionRequest
from common_functions import save_geojson


class TestSegmentationPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = pointPredictor

        request_data = {
            "zoom_level": 21,
            "box_threshold": 0.24,
            "points_include": [[-96.78735903257792,32.76919652798132],[-96.78694633366432,32.76941409030799],[-96.78693217686015,32.76888747455614],[-96.78506568738678,32.76824808468834]],
            "points_exclude":[]
        }                
        self.request = PointPredictionRequest(**request_data)

    def test_points_predict_success(self):
        
        request = self.request
        result = asyncio.run(self.predictor.make_prediction(
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
            points_include=request.points_include,
            points_exclude=request.points_exclude
        ))
        
        # Validate result structure
        self.assertIsNotNone(result, "Result should not be None")
        self.assertIsNotNone(result['geojson'], "GeoJSON should not be None")
        # Save the GeoJSON result
        save_geojson(
            result['geojson'], 
            f"points_detection_{request.zoom_level}"
        )
        print(len(result['geojson']['features']))
        
        self.assertEqual(result['geojson']['type'], 'FeatureCollection', "Type should be FeatureCollection")
        self.assertGreater(len(result['geojson']['features']), 0, "Should have at least one feature")
        self.assertEqual(len(result['geojson']['features']), 4, "Should be 4 features")

if __name__ == "__main__":
    unittest.main()


    