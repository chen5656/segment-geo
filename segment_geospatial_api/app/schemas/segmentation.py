from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str


class SegmentationGeojsonResults(BaseModel):
    errors: Optional[Any]
    version: str
    predictions: Optional[str]
    geojson: Optional[dict]


class SegmentationWithTextPromptRequest(BaseModel):
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
                "zoom_level": 19,
                "box_threshold": 0.24,
                "text_threshold": 0.24
            }
        }


class SegmentationWithPointsRequest(BaseModel):
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
    points_include: List[List[float]] = Field(
        default=[],
        description="List of points to include in the segmentation",
        example=[[-96.81040, 32.97140]]
    )
    points_exclude: List[List[float]] = Field(
        default=[],
        description="List of points to exclude from the segmentation",
        example=[[-96.81000, 32.97180]]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "zoom_level": 20,
                "box_threshold": 0.24,
                "points_include": [
                    [-96.75957441329956, 32.77962558419501],
                    [-96.76011219620706, 32.77979697101114],
                    [-96.75975278019907, 32.780051795535265],
                    [-96.75899103283884, 32.77942713589021],
                    [-96.75938665866852, 32.779101273793295]
                ],
                "points_exclude": []
            }
        }   
