import os
import sys
import asyncio
import glob
import json
from datetime import datetime

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from app.segment_geospatial.predict import predictor
from app.schemas.predict import PredictionRequest

def save_geojson(data, prefix="test_result"):
    """Save GeoJSON data to a file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.geojson"
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(project_root, "test_results")
    os.makedirs(results_dir, exist_ok=True)
    
    filepath = os.path.join(results_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"GeoJSON saved to: {filepath}")
    return filepath

async def call_predict(request: PredictionRequest):
    try:        
        _result = await predictor.make_prediction(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            zoom_level=request.zoom_level,
        )
        return _result
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise

if __name__ == "__main__":
    # [min_longitude, min_latitude, max_longitude, max_latitude]
    # [left, bottom, right, top]
    request_data = {
        "bounding_box": [
            -96.77738159894946,
            32.78197733203472,
            -96.77620947360994,
            32.78268991937202
        ],
        "text_prompt": "car",
        "zoom_level": 19
    }
    
    request = PredictionRequest(**request_data)
    
    # Run the async function
    result = asyncio.run(call_predict(request))
    
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
        saved_file = save_geojson(
            result['geojson'], 
            f"trees_detection_{request.zoom_level}"
        )
        print(f"Found {len(result['geojson']['features'])} features")
     
    # Verify temporary files are cleaned up
    temp_files = glob.glob("*.tif") + glob.glob("*.geojson")
    assert len(temp_files) == 0, f"Found temporary files that were not deleted: {temp_files}"
    
    print("All assertions passed!")
