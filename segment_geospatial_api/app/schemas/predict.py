from typing import Any, List, Optional, Dict, Union

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str


class PredictionResults(BaseModel):
    errors: Optional[Any]
    version: str
    predictions: Optional[List[int]]
    geojson: Optional[dict]


class PredictionRequest(BaseModel):
    bounding_box: List[float] = Field(
        default=[-122.4194, 37.7749, -122.4094, 37.7849],
        description="Bounding box coordinates [west, south, east, north]",
        example=[-122.4194, 37.7749, -122.4094, 37.7849]
    )
    text_prompt: str = Field(
        default="trees",
        description="Text description of the features to detect",
        example="trees"
    )
    zoom_level: int = Field(
        default=20,
        description="Zoom level for satellite imagery (1-22)",
        ge=1,
        le=22
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bounding_box": [-122.4194, 37.7749, -122.4094, 37.7849],
                "text_prompt": "trees",
                "zoom_level": 20
            }
        }