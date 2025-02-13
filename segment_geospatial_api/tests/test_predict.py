import sys
import pytest
import asyncio
import glob
import json
from datetime import datetime
from pathlib import Path


# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.segment_geospatial.predict import SegmentationPredictor
from app.schemas.segmentation import SegmentationWithTextPromptRequest, SegmentationWithPointsRequest

@pytest.fixture
def predictor():
    """Fixture to create and setup predictor instance"""
    pred = SegmentationPredictor()
    pred.setup("sam2-hiera-tiny")
    return pred

@pytest.fixture
def test_results_dir():
    """Fixture to create and manage test results directory"""
    results_dir = project_root / "tests" / "test_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir

@pytest.fixture
def sample_request():
    """Fixture for sample request data"""
    return SegmentationWithTextPromptRequest(
        bounding_box=[
            -96.78806887088176,
            32.76760907972303,
            -96.78423468921088,
            32.769729127062774
        ],
        text_prompt="buildings",
        zoom_level=18,
        box_threshold=0.4,
        text_threshold=0.24,
    )

def save_geojson(data, prefix: str, results_dir: Path):
    """Helper function to save GeoJSON results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.geojson"
    filepath = results_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath

class TestSegmentationPredictor:
    
    @pytest.mark.asyncio
    async def test_segment_with_text_prompt_basic(self, predictor, sample_request, test_results_dir):
        """Test basic functionality of segment_with_text_prompt"""
        result = await predictor.segment_with_text_prompt(
            bounding_box=sample_request.bounding_box,
            text_prompt=sample_request.text_prompt,
            zoom_level=sample_request.zoom_level,
            box_threshold=sample_request.box_threshold,
            text_threshold=sample_request.text_threshold,
        )
        
        # Validate result structure
        assert result is not None
        assert 'geojson' in result
        assert result['geojson']['type'] == 'FeatureCollection'
        assert len(result['geojson']['features']) > 0

    @pytest.mark.asyncio
    async def test_segment_with_text_prompt_feature_structure(self, predictor, sample_request):
        """Test the structure of returned features"""
        result = await predictor.segment_with_text_prompt(
            bounding_box=sample_request.bounding_box,
            text_prompt=sample_request.text_prompt,
            zoom_level=sample_request.zoom_level,
            box_threshold=sample_request.box_threshold,
            text_threshold=sample_request.text_threshold,
        )
        
        feature = result['geojson']['features'][0]
        assert feature['type'] == 'Feature'
        assert feature['geometry']['type'] == 'Polygon'
        assert 'coordinates' in feature['geometry']

    @pytest.mark.asyncio
    @pytest.mark.parametrize("text_prompt,min_features", [
        ("buildings", 1),
        ("trees", 1),
        ("roads", 1),
    ])
    async def test_segment_with_different_prompts(
        self, predictor, sample_request, text_prompt, min_features
    ):
        """Test segmentation with different text prompts"""
        sample_request.text_prompt = text_prompt
        result = await predictor.segment_with_text_prompt(
            bounding_box=sample_request.bounding_box,
            text_prompt=sample_request.text_prompt,
            zoom_level=sample_request.zoom_level,
            box_threshold=sample_request.box_threshold,
            text_threshold=sample_request.text_threshold,
        )
        
        assert len(result['geojson']['features']) >= min_features

    @pytest.mark.asyncio
    async def test_cleanup(self, predictor, sample_request):
        """Test that temporary files are cleaned up after processing"""
        await predictor.segment_with_text_prompt(
            bounding_box=sample_request.bounding_box,
            text_prompt=sample_request.text_prompt,
            zoom_level=sample_request.zoom_level,
            box_threshold=sample_request.box_threshold,
            text_threshold=sample_request.text_threshold,
        )
        
        # Check for temporary files
        temp_files = list(Path().glob("*.tif")) + list(Path().glob("*.geojson"))
        assert len(temp_files) == 0, f"Found temporary files that were not deleted: {temp_files}"

    @pytest.mark.asyncio
    async def test_invalid_bounding_box(self, predictor):
        """Test handling of invalid bounding box"""
        invalid_request = SegmentationWithTextPromptRequest(
            bounding_box=[0, 0, 0, 0],  # Invalid bounding box
            text_prompt="buildings",
            zoom_level=18,
            box_threshold=0.4,
            text_threshold=0.24,
        )
        
        with pytest.raises(Exception):
            await predictor.segment_with_text_prompt(
                bounding_box=invalid_request.bounding_box,
                text_prompt=invalid_request.text_prompt,
                zoom_level=invalid_request.zoom_level,
                box_threshold=invalid_request.box_threshold,
                text_threshold=invalid_request.text_threshold,
            )

    @pytest.mark.asyncio
    async def test_end_to_end_prediction(self, predictor, test_results_dir):
        """Test end-to-end prediction workflow"""
        # Setup test request
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
        
        # Run prediction
        result = await predictor.segment_with_text_prompt(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
        )
        
        # Validate results
        assert result is not None
        assert result['geojson'] is not None
        assert result['geojson']['type'] == 'FeatureCollection'
        assert len(result['geojson']['features']) > 0
        
        # Validate feature structure
        feature = result['geojson']['features'][0]
        assert feature['type'] == 'Feature'
        assert feature['geometry']['type'] == 'Polygon'
        
        # Save results if needed
        if result['geojson']:
            saved_file = save_geojson(
                result['geojson'],
                f"buildings_detection_{request.zoom_level}",
                test_results_dir
            )
            
        # Verify cleanup
        temp_files = list(Path().glob("*.tif")) + list(Path().glob("*.geojson"))
        assert len(temp_files) == 0, f"Found temporary files that were not deleted: {temp_files}"

async def call_predict_segment_with_text_prompt(request: SegmentationWithTextPromptRequest):
    try:        
        _result = await predictor.segment_with_text_prompt(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,  
        )
        return _result
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise
