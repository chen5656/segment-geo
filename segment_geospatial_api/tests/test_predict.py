import os
import sys
import asyncio
import glob

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from app.segment_geospatial.predict import predictor
from app.schemas.predict import PredictionRequest

async def call_predict(request: PredictionRequest):
    try:        
        _result = await predictor.make_prediction(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            zoom_level=request.zoom_level
        )
        return _result
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise

if __name__ == "__main__":
    request = PredictionRequest(
        bounding_box=[-122.4194, 37.7749, -122.4094, 37.7849],
        text_prompt="trees",
        zoom_level=20
    )
    
    # Run the async function
    result = asyncio.run(call_predict(request))
    print(result)
    
    # Validate result structure
    assert result is not None
    assert result['geojson'] is not None
    assert result['geojson']['type'] == 'FeatureCollection'
    assert len(result['geojson']['features']) > 0
    
    # Validate feature structure
    feature = result['geojson']['features'][0]
    assert feature['type'] == 'Feature'
    assert feature['geometry']['type'] == 'Polygon'
    assert feature['geometry']['coordinates'] is not None
    assert feature['properties']['class'] == 'tree'
    
    # Verify temporary files are cleaned up
    temp_files = glob.glob("*.tif") + glob.glob("*.geojson")
    assert len(temp_files) == 0, f"Found temporary files that were not deleted: {temp_files}"
    
    print("All assertions passed!")
