from typing import Any, List, Optional, Union

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
        default=[-96.81040, 32.97140, -96.81000, 32.97180],
        description="Bounding box coordinates [west, south, east, north]",
        example=[-96.81040, 32.97140, -96.81000, 32.97180]
    )
    text_prompt: str = Field(
        default="trees",
        description="Text description of the features to detect",
        example="trees"
    )
    zoom_level: int = Field(
        default=19,
        description="Zoom level for satellite imagery (1-20), 20 may not work",
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