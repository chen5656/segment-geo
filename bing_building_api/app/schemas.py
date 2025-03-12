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


class GeometryInput(BaseModel):
    """GeoJSON geometry schema"""
    type: str = Field(..., description="GeoJSON geometry type", 
                     pattern="^(Point|MultiPoint|LineString|MultiLineString|Polygon|MultiPolygon)$")
    coordinates: List[Any] = Field(..., description="GeoJSON coordinates array")

    class Config:
        schema_extra = {
            "example": {
                "type": "Polygon",
                "coordinates": [[[30.0, 10.0], [40.0, 40.0], [20.0, 40.0], [10.0, 20.0], [30.0, 10.0]]]
            }
        }

class BatchGeometryRequest(BaseModel):
    geometries: List[GeometryInput]


