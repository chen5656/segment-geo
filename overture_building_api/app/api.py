from typing import Union
import tempfile
import os
import time
from functools import wraps

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from loguru import logger

from app import schemas
from app.config import settings
from geoai.download import (
    download_naip,
    download_overture_buildings,
    extract_building_stats,
)
from app.services.building_service import get_building_data

api_router = APIRouter()

def retry_on_network_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "NETWORK_CONNECTION" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"Network error, retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    raise
            return None
        return wrapper
    return decorator

@api_router.get("/health", response_model=schemas.Health, status_code=200)
def health() -> dict:
    """
    Health check endpoint
    """
    health = schemas.Health(
        name=settings.PROJECT_NAME, 
        api_version=settings.API_VERSION
    )
    return health.model_dump()


@api_router.post("/buildings",
                response_model=Union[schemas.BuildingResponse, schemas.ErrorResponse],
                status_code=200)
async def get_buildings(request: schemas.BuildingRequest):
    try:
        result = await get_building_data(request.bbox)
        return JSONResponse(
            status_code=200,
            content=result
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": f"{e}"}}
        )
        
    return schemas.BuildingResponse(**result["data"])