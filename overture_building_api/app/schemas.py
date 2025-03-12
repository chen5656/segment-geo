from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Health(BaseModel):
    """Health check response schema"""
    name: str
    api_version: str


class BuildingRequest(BaseModel):
    """Request schema for building footprint endpoint"""
    bbox: List[float] = Field(
        ...,
        description="Bounding box coordinates [min_lon, min_lat, max_lon, max_lat]",
        min_items=4,
        max_items=4
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bbox": [-76.15741548689954, 43.05635088078997, -76.15648427005196, 43.05692144640927]
            }
        }


class BuildingStats(BaseModel):
    """Statistics about the buildings in the response"""
    total_buildings: int
    has_height: int
    has_name: int
    bbox: List[float]


class BuildingResponse(BaseModel):
    """Response schema for building footprint endpoint"""
    geojson: Dict[str, Any]
    stats: BuildingStats


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: Dict[str, str]