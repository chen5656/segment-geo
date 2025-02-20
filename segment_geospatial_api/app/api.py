from typing import Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from segment_geospatial_api.app.segment_geospatial.predict import textPredictor
from app.segment_geospatial.point_predict import pointPredictor
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

@api_router.post("/predict", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200,
                deprecated=True)
@api_router.post("/predict/text", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200)
async def predict_text(request: schemas.PredictionRequest):
    try:
        result = await textPredictor.make_prediction(
            bounding_box=request.bounding_box,
            text_prompt=request.text_prompt,
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
            text_threshold=request.text_threshold,
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

@api_router.post("/predict/points", 
                response_model=Union[schemas.PredictionResults, schemas.ErrorResponse], 
                status_code=200)
async def predict_with_points(request: schemas.PointPredictionRequest):
    try:
        result = await pointPredictor.make_prediction(
            points_include=request.points_include,
            points_exclude=request.points_exclude,
            zoom_level=request.zoom_level,
            box_threshold=request.box_threshold,
        )
        if result.get("error") is not None:
            logger.warning(f"Point prediction validation error: {result.get('error')}")
            return JSONResponse(
                status_code=400,
                content={"error": {"message": result["error"]}}
            )

        logger.info(f"Point prediction results: {result.get('predictions')}")
        return JSONResponse(
            status_code=200,
            content=result.get("geojson")
        )

    except Exception as e:
        logger.error(f"Error during point prediction: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e)}}
        )
