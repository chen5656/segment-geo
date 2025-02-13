from typing import Union
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.segment_geospatial.predict import predictor
from loguru import logger
from app.retry.retry import retry_prediction

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

@api_router.post("/segment/text_prompt", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200)
async def segment_with_text_prompt(request: schemas.SegmentationWithTextPromptRequest):
    """
    Perform segmentation using a text prompt to identify target areas
    """
    try:
        # Create callback function that captures the request parameters
        async def prediction_callback():
            return await predictor.segment_with_text_prompt(
                bounding_box=request.bounding_box,
                text_prompt=request.text_prompt,
                zoom_level=request.zoom_level,
                box_threshold=request.box_threshold,
                text_threshold=request.text_threshold,
            )
        
        result = await retry_prediction(prediction_callback)
        
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

@api_router.post("/segment/interactive", 
                response_model=Union[schemas.SegmentationGeojsonResults, schemas.ErrorResponse], 
                status_code=200)
async def segment_interactive(request: schemas.SegmentationWithPointsRequest):
    """
    Perform interactive segmentation using include/exclude points
    """
    try:
        async def points_prediction_callback():
            return await predictor.segment_with_points(
                bounding_box=request.bounding_box,
                text_prompt=request.text_prompt,
                zoom_level=request.zoom_level,
                box_threshold=request.box_threshold,
                points_include=request.points_include,
                points_exclude=request.points_exclude
            )
            
        result = await retry_prediction(points_prediction_callback)
        
        if result is None:
            return JSONResponse(
                status_code=400,
                content={"error": {"message": "Failed to download satellite imagery after multiple retries"}}
            )
            
        return result
    except Exception as e:
        logger.error(f"Error during segmentation with points: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e)}}
        )