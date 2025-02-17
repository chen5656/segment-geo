import os
import sys
from loguru import logger
import sys
import asyncio
# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from app.predict.predict import SegmentationPredictor
from app.schemas.segmentation import SegmentationWithPointsRequest
from common_functions import save_geojson


class TestSegmentationPredictor:
    def __init__(self):
        self.predictor = SegmentationPredictor()
        logger.info(f"Using LangSAM model: {self.predictor.point_predictor.model_type}")

    async def test_predict_segment_with_points_success(self, request):
        
        # Run the async function
        result = await self.predictor.segment_with_points(
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
            points_include=request.points_include,
            points_exclude=request.points_exclude
        )
        
        # Validate result structure
        assert result is not None
        assert result['geojson'] is not None
        assert result['geojson']['type'] == 'FeatureCollection'
        assert len(result['geojson']['features']) > 0
        
        # Save the GeoJSON result
        save_geojson(
            result['geojson'], 
            f"points_detection_{request.zoom_level}"
        )

        # Validate feature structure
        feature = result['geojson']['features'][0]
        assert feature['type'] == 'Feature'
        assert feature['geometry']['type'] == 'Polygon'
        assert len(result['geojson']['features']) < 4 
        
        print(f"Found {len(result['geojson']['features'])} features")
        # Found 242 features is wrong
                
        print("All assertions passed!")

if __name__ == "__main__":


    request_data = {
        "zoom_level": 21,
        "box_threshold": 0.24,
        "points_include": [[-96.78735903257792,32.76919652798132],[-96.78694633366432,32.76941409030799],[-96.78693217686015,32.76888747455614],[-96.78506568738678,32.76824808468834]],
        "points_exclude":[]
    }    
        
    request = SegmentationWithPointsRequest(**request_data)
    
    seg = TestSegmentationPredictor()
    asyncio.run(seg.test_predict_segment_with_points_success(request))

    