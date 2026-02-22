from fastapi import APIRouter, HTTPException
from app.api.schemas import (
    RecommendRequest, RecommendResponse, PlaceResult, ScoreBreakdown,
    FeedbackRequest, FeedbackResponse, HealthResponse
)
from app.services.places_provider import fetch_places
from app.services.ranker import rank_places
from app.services.personalization import get_user_profile, save_feedback, clear_user_feedback

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
)
async def health():
    return HealthResponse(
        status="ok",
        version="2.0.0",
        embedding_model="all-MiniLM-L6-v2",
    )


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    tags=["Recommendations"],
    summary="Get personalized place recommendations",
    description=(
        "Fetches nearby places from OpenStreetMap and ranks them using a hybrid scoring system "
        "combining semantic similarity, distance, keyword matching, and user personalization."
    ),
)
async def recommend(req: RecommendRequest):
    # Fetch places from Overpass API
    try:
        places = await fetch_places(req.lat, req.lng, req.radius_m)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not places:
        return RecommendResponse(
            query=req.query,
            total_fetched=0,
            total_returned=0,
            results=[]
        )

    # Load personalization profile if user_id provided
    user_profile = {}
    if req.user_id:
        user_profile = get_user_profile(req.user_id)

    # Rank places using hybrid scoring
    ranked = rank_places(
        query=req.query,
        user_lat=req.lat,
        user_lng=req.lng,
        radius_m=req.radius_m,
        places=places,
        user_profile=user_profile,
        max_results=req.max_results,
    )

    results = [
        PlaceResult(
            place_id=p["place_id"],
            name=p["name"],
            category=p["category"],
            lat=p["lat"],
            lng=p["lng"],
            distance_m=p["distance_m"],
            tags=p["tags"],
            score=ScoreBreakdown(**p["score"]),
        )
        for p in ranked
    ]

    return RecommendResponse(
        query=req.query,
        total_fetched=len(places),
        total_returned=len(results),
        results=results,
    )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    tags=["Personalization"],
    summary="Submit feedback on a place",
    description="Records a like, dislike, or click. Used to personalize future recommendations.",
)
async def submit_feedback(req: FeedbackRequest):
    save_feedback(req.user_id, req.place_id, req.action.value, req.category_hint)
    return FeedbackResponse(success=True, message="Feedback recorded.")


@router.delete(
    "/feedback/{user_id}",
    response_model=FeedbackResponse,
    tags=["Personalization"],
    summary="Clear all feedback for a user",
)
async def clear_feedback(user_id: str):
    clear_user_feedback(user_id)
    return FeedbackResponse(success=True, message=f"Feedback cleared for user '{user_id}'.")