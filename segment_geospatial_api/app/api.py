import json
from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.segment_geospatial.predict import predictor
from loguru import logger
from pydantic import BaseModel, Field

from app import __version__, schemas
from app.config import settings

api_router = APIRouter()

class PredictionRequest(BaseModel):
    bounding_box: list = Field(..., description="Coordinates [west, south, east, north]")
    text_prompt: str = Field(..., description="Text description of object to detect")
    box_threshold: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Confidence threshold for object detection boxes (0-1)"
    )
    text_threshold: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Confidence threshold for text-to-image matching (0-1)"
    )
    zoom_level: int = Field(
        default=20, 
        ge=1, 
        le=22, 
        description="Zoom level for satellite imagery"
    )

@api_router.get("/health", response_model=schemas.Health, status_code=200)
def health() -> dict:
    """
    Root Get
    """
    health = schemas.Health(
        name=settings.PROJECT_NAME, api_version=__version__
    )
    return health.dict()

@api_router.post("/predict", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200)
async def predict(request: PredictionRequest):
    try:
        result = await predictor.make_prediction(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
            zoom_level=request.zoom_level
        )

        if result.get("errors") is not None:
            logger.warning(f"Prediction validation error: {result.get('errors')}")
            return JSONResponse(
                status_code=400,
                content={"error": str(result["errors"])}
            )

        logger.info(f"Prediction results: {result.get('predictions')}")
        return result  # FastAPI will automatically convert this to JSONResponse

    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@api_router.post("/predict/batch", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200)
async def predict_batch(request: PredictionRequest):
    """Endpoint for batch prediction without merging tiles."""
    try:
        result = await predictor.make_batch_prediction(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
            zoom_level=request.zoom_level
        )

        if "error" in result:
            logger.warning(f"Batch prediction error: {result['error']}")
            return JSONResponse(
                status_code=400,
                content={"error": result["error"]}
            )

        logger.info(f"Batch prediction completed successfully")
        return result

    except Exception as e:
        logger.error(f"Error during batch prediction: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        ) 