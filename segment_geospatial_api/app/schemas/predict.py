from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str


class PredictionResults(BaseModel):
    errors: Optional[Any]
    version: str
    predictions: Optional[str]
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
    box_threshold: float = Field(
        default=0.24,
        description="Confidence threshold for object detection boxes (0-1)",
        ge=0,
        le=1
    )
    text_threshold: float = Field(
        default=0.24,
        description="Confidence threshold for text-to-image matching (0-1)",
        ge=0,
        le=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bounding_box": [-96.81040, 32.97140, -96.81000, 32.97180],
                "text_prompt": "trees",
                "zoom_level": 20,
                "box_threshold": 0.24,
                "text_threshold": 0.24
            }
        }


class PointPredictionRequest(BaseModel):
    points_include: List[List[float]] = Field(
        description="List of points to include [lon, lat]"
    )
    points_exclude: Optional[List[List[float]]] = Field(
        default=None,
        description="List of points to exclude [lon, lat]"
    )
    zoom_level: int = Field(
        default=19,
        description="Zoom level for satellite imagery",
        ge=1,
        le=22
    )
    box_threshold: float = Field(
        default=0.3,
        description="Confidence threshold for object detection boxes",
        ge=0,
        le=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "points_include": [[-96.81020, 32.97160], [-96.81030, 32.97170]],
                "points_exclude": [[-96.81010, 32.97150], [-96.81040, 32.97180]],
                "zoom_level": 20,
                "box_threshold": 0.3
            }
        }