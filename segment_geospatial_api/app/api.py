import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from .predict import predictor
from loguru import logger

from app import __version__, schemas
from app.config import settings


api_router = APIRouter()


@api_router.get("/health", response_model=schemas.Health, status_code=200)
def health() -> dict:
    """
    Root Get
    """
    health = schemas.Health(
        name=settings.PROJECT_NAME, api_version=__version__
    )

    return health.dict()

@api_router.post("/predict", response_model=schemas.PredictionResults, status_code=200)
async def predict(request: schemas.PredictionRequest):
    result = await predictor.make_prediction(
        bounding_box=request.bounding_box,
        text_prompt=request.text_prompt,
        zoom_level=request.zoom_level
    )

    if result["errors"] is not None:
        logger.warning(f"Prediction validation error: {result.get('errors')}")
        raise HTTPException(status_code=400, detail=json.loads(result["errors"]))

    logger.info(f"Prediction results: {result.get('predictions')}")

    return result 