from typing import Any, List, Tuple, Optional

from pydantic import BaseModel


class PredictionResults(BaseModel):
    errors: Optional[Any]
    version: str
    predictions: Optional[List[int]]


class PredictionRequest(BaseModel):
    bounding_box: Tuple[float, float, float, float]
    text_prompt: str
    zoom_level: int = 20