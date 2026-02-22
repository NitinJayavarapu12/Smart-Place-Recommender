from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ── Request Models ──────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="User latitude")
    lng: float = Field(..., ge=-180, le=180, description="User longitude")
    query: str = Field(..., min_length=1, max_length=300, description="Natural language query")
    radius_m: int = Field(1500, ge=100, le=10000, description="Search radius in meters")
    max_results: int = Field(10, ge=1, le=30, description="Max number of results")
    open_now: bool = Field(False, description="Filter to open places only (best effort)")
    user_id: Optional[str] = Field(None, description="User ID for personalization")

    model_config = {
        "json_schema_extra": {
            "example": {
                "lat": 40.7128,
                "lng": -74.0060,
                "query": "quiet coffee shop to work",
                "radius_m": 1500,
                "max_results": 10,
                "open_now": False,
                "user_id": "user_123"
            }
        }
    }


class FeedbackAction(str, Enum):
    like = "like"
    dislike = "dislike"
    click = "click"


class FeedbackRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    place_id: str = Field(..., description="Place ID (e.g. osm:node:123456)")
    action: FeedbackAction = Field(..., description="User action")
    category_hint: Optional[str] = Field(None, description="Category hint (e.g. amenity:cafe)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user_123",
                "place_id": "osm:node:123456",
                "action": "like",
                "category_hint": "amenity:cafe"
            }
        }
    }


# ── Response Models ──────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    semantic: float = Field(..., description="Semantic similarity score (0-1)")
    distance: float = Field(..., description="Distance score (0-1, closer = higher)")
    keyword: float = Field(..., description="Keyword boost score (0-1)")
    personalization: float = Field(..., description="Personalization boost score (0-1)")
    final: float = Field(..., description="Final weighted score (0-1)")


class PlaceResult(BaseModel):
    place_id: str
    name: str
    category: str
    lat: float
    lng: float
    distance_m: float
    tags: dict
    score: ScoreBreakdown


class RecommendResponse(BaseModel):
    query: str
    total_fetched: int
    total_returned: int
    results: list[PlaceResult]


class FeedbackResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    embedding_model: str