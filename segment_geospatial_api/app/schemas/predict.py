from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str


class PredictionResults(BaseModel):
    errors: Optional[Any]
    version: str
    predictions: Optional[str]
    geojson: Optional[dict]


class PromptConfig(BaseModel):
    value: str = Field(..., description="Text prompt for detection")
    text_threshold: float = Field(default=0.25, description="Text threshold for this specific prompt")
    box_threshold: float = Field(default=0.3, description="Box threshold for this specific prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "value": "trees",
                "text_threshold": 0.25,
                "box_threshold": 0.3
            }
        }


class PredictionRequest(BaseModel):
    bounding_box: List[float] = Field(..., description="Bounding box coordinates [min_lon, min_lat, max_lon, max_lat]")
    zoom_level: int = Field(..., description="Zoom level for the map")
    text_prompts: List[PromptConfig] = Field(..., description="List of prompts with their individual thresholds")

    class Config:
        json_schema_extra = {
            "example": {
                "bounding_box": [-96.81040, 32.97140, -96.81000, 32.97180],
                "zoom_level": 20,
                "text_prompts": [
                    {"value": "trees", "text_threshold": 0.25, "box_threshold": 0.3},
                    {"value": "buildings", "text_threshold": 0.25, "box_threshold": 0.3}
                ]
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