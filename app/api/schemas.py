from pydantic import BaseModel
from typing import List, Optional

class PlaceOut(BaseModel):
    place_id: str
    name: str
    address: Optional[str] = None
    lat: float
    lng: float
    categories: List[str] = []
    distance_m: Optional[float] = None
    semantic_score: Optional[float] = None
    personal_boost: Optional[float] = None
    score: float

class RecommendResponse(BaseModel):
    results: List[PlaceOut]

class FeedbackResponse(BaseModel):
    status: str
