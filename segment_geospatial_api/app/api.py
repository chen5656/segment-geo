from typing import Union
import asyncio
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.segment_geospatial.predict import predictor
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

async def retry_prediction(request: schemas.PredictionRequest, max_retries: int = 3, delay: float = 1.0):
    """
    Retry the prediction with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            result = await predictor.make_prediction(
                bounding_box=request.bounding_box,
                text_prompt=request.text_prompt,
                zoom_level=request.zoom_level,
                box_threshold=request.box_threshold,
                text_threshold=request.text_threshold,
            )
            return result
        except Exception as e:
            if "Failed to download satellite imagery" in str(e):
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
            raise e
    return None

@api_router.post("/predict", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200)
async def predict(request: schemas.PredictionRequest):
    try:
        result = await retry_prediction(request)
        
        if result is None:
            return JSONResponse(
                status_code=400,
                content={"error": {"message": "Failed to download satellite imagery after multiple retries"}}
            )

        if result.get("error") is not None:
            logger.warning(f"Prediction validation error: {result.get('error')}")
            error_content = result["error"]
            # Handle both simple string errors and structured error objects
            if isinstance(error_content, str):
                return JSONResponse(
                    status_code=400,
                    content={"error": {"message": error_content}}
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={"error": error_content}
                )

        logger.info(f"Prediction results: {result.get('predictions')}")
        
        return JSONResponse(
            status_code=200,
            content=result.get("geojson")
        )

    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e)}}
        )
