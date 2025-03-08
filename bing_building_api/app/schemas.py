from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Health(BaseModel):
    """Health check response schema"""
    name: str
    api_version: str

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: Dict[str, str]

class BuildingResponse(BaseModel):
    """Building query response schema"""
    type: str = Field(default="FeatureCollection")
    features: List[Dict[str, Any]]

class DownloadResponse(BaseModel):
    """Download response schema"""
    status: str
    downloaded: List[str]


