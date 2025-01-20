import json
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import PredictionRequest

client = TestClient(app)

def test_health():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "segment-geospatial-api"
    assert "api_version" in data

@pytest.fixture
def mock_prediction_result():
    return {
        "geojson": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                    },
                    "properties": {"class": "tree"}
                }
            ]
        },
        "errors": None
    }

@pytest.mark.asyncio
async def test_predict_success(mock_prediction_result):
    """Test successful prediction"""
    request_data = {
        "bounding_box": [-122.4194, 37.7749, -122.4094, 37.7849],
        "text_prompt": "trees",
        "zoom_level": 20
    }

    with patch('app.api.predictor.make_prediction') as mock_predict:
        mock_predict.return_value = mock_prediction_result
        response = client.post("/api/v1/predict", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["geojson"]["type"] == "FeatureCollection"
    assert len(data["geojson"]["features"]) > 0
    assert data["errors"] is None

@pytest.mark.asyncio
async def test_predict_validation_error():
    """Test prediction with validation error"""
    request_data = {
        "bounding_box": [-122.4194, 37.7749, -122.4094, 37.7849],
        "text_prompt": "trees",
        "zoom_level": 20
    }

    error_result = {
        "geojson": None,
        "errors": json.dumps({"error": "Validation error"})
    }

    with patch('app.api.predictor.make_prediction') as mock_predict:
        mock_predict.return_value = error_result
        response = client.post("/api/v1/predict", json=request_data)
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"] == "Validation error"

def test_predict_invalid_input():
    """Test prediction with invalid input"""
    # Missing required fields
    request_data = {
        "text_prompt": "trees"
    }
    
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 422  # Unprocessable Entity

    # Invalid bounding box format
    request_data = {
        "bounding_box": [-122.4194],  # Should be 4 coordinates
        "text_prompt": "trees",
        "zoom_level": 20
    }
    
    response = client.post("/api/v1/predict", json=request_data)
    assert response.status_code == 422
