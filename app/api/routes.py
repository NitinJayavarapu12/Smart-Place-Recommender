from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.api.schemas import RecommendResponse, FeedbackResponse
from app.services.places_provider import fetch_places
from app.services.ranker import rank_places
from app.services.personalization import get_user_category_boosts
from app.db.database import SessionLocal
from app.db.models import Feedback

router = APIRouter(tags=["Recommender"])
feedback_router = APIRouter(tags=["Feedback"])


class RecommendRequest(BaseModel):
    lat: float = Field(..., examples=[30.4213])
    lng: float = Field(..., examples=[-87.2169])
    query: str = Field(..., examples=["quiet coffee shop to work"])
    radius_m: int = Field(default=2000, ge=100, le=20000, examples=[2000])
    max_results: int = Field(default=5, ge=1, le=25, examples=[5])
    categories: Optional[List[str]] = Field(default=None, examples=[["cafe", "restaurant"]])
    open_now: bool = Field(default=True, examples=[True])
    user_id: Optional[str] = Field(default=None, examples=["nitin_test"])

class FeedbackRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    place_id: str = Field(..., min_length=1, max_length=128)
    action: str = Field(..., pattern="^(like|dislike|click)$")
    category_hint: Optional[str] = None

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    try:
        places = fetch_places(
            lat=req.lat,
            lng=req.lng,
            radius_m=req.radius_m,
            categories=req.categories,
            open_now=req.open_now,
        )

        boosts = {}
        if req.user_id:
            db = SessionLocal()
            try:
                boosts = get_user_category_boosts(db, req.user_id)
            finally:
                db.close()

        ranked = rank_places(
            user_lat=req.lat,
            user_lng=req.lng,
            user_query=req.query,
            places=places,
            radius_m=req.radius_m,
            user_boosts=boosts,
        )

        return {"results": ranked[: req.max_results]}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@feedback_router.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest):
    db = SessionLocal()
    try:
        row = Feedback(
            user_id=req.user_id,
            place_id=req.place_id,
            action=req.action,
            category_hint=req.category_hint,
        )
        db.add(row)
        db.commit()
        return {"status": "saved"}
    finally:
        db.close()

@feedback_router.delete("/feedback/{user_id}")
def clear_feedback(user_id: str):
    db = SessionLocal()
    try:
        db.query(Feedback).filter(Feedback.user_id == user_id).delete()
        db.commit()
        return {"status": "cleared"}
    finally:
        db.close()

