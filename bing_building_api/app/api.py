from typing import Union
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from shapely.geometry import shape, box
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from loguru import logger
import json

from app import schemas
from app.config import settings
from app.services.query import BingBuildingQuery
from app.services.downloader import BingBuildingDownloader

api_router = APIRouter()

@api_router.get("/")
async def root():
    """
    Serve the index.html file
    """
    return FileResponse('app/static/index.html')

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

@api_router.post('/query/buildings',
                response_model=Union[schemas.BuildingResponse, schemas.ErrorResponse],
                status_code=200)
async def query_buildings(request: schemas.BatchGeometryRequest):
    try:
        query_engine = BingBuildingQuery()
        results = query_engine.query_buildings(request.geometries)
        return JSONResponse(content=json.loads(results))
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=400,
            content={"error": {"message": str(e)}}
        )

@api_router.post('/download/buildings',
                response_model=Union[schemas.DownloadResponse, schemas.ErrorResponse],
                status_code=200)
async def download_building_tiles(request: schemas.BatchGeometryRequest):
    try:       
        downloader = BingBuildingDownloader()
        results = await downloader.download_buildings(request.geometries)
        return JSONResponse(
            content={"status": "success", "downloaded": results}
        )
    except Exception as e:
        logger.error(f"Error downloading buildings: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": {"message": f"{e}"}}
        )
