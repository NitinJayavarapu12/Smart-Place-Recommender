from typing import List, Dict, Any, Optional
from app.utils.geo import haversine_m
from app.services.embedder import embed_texts, cosine_sim_matrix

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def score_distance(distance_m: float, radius_m: int) -> float:
    """
    1.0 when very close, down to ~0.0 near radius limit.
    """
    if radius_m <= 0:
        return 0.0
    return clamp(1.0 - (distance_m / float(radius_m)), 0.0, 1.0)

def score_category_match(place_categories: List[str], query: str) -> float:
    """
    Simple keyword match. Later we’ll replace with embeddings.
    """
    q = query.lower()
    # tiny heuristic: if query mentions coffee, prefer cafes
    boosts = {
        "coffee": ["amenity:cafe"],
        "cafe": ["amenity:cafe"],
        "pizza": ["amenity:restaurant"],
        "work": ["amenity:cafe", "amenity:library"],
        "quiet": ["amenity:library", "amenity:cafe"],
    }

    wanted = []
    for k, v in boosts.items():
        if k in q:
            wanted.extend(v)

    if not wanted:
        return 0.0

    hit = any(cat in place_categories for cat in wanted)
    return 1.0 if hit else 0.0

def place_text_profile(p: Dict[str, Any]) -> str:
    """
    Turn a place into a text string for semantic matching.
    Keep it simple but informative.
    """
    name = p.get("name") or ""
    cats = " ".join(p.get("categories") or [])
    addr = p.get("address") or ""
    return f"{name}. Categories: {cats}. Address: {addr}".strip()

def rank_places(
    user_lat: float,
    user_lng: float,
    user_query: str,
    places: List[Dict[str, Any]],
    radius_m: int,
    user_boosts: Optional[dict] = None,
) -> List[Dict[str, Any]]:
    ranked = []

    # --- Semantic embeddings (AI part) ---
    profiles = [place_text_profile(p) for p in places]
    # Embed [query] + [profiles...]
    vecs = embed_texts([user_query] + profiles)
    qvec = vecs[0]
    pvecs = vecs[1:]

    sem_sims = cosine_sim_matrix(qvec, pvecs)  # values roughly [-1, 1], but mostly [0, 1]
    # normalize semantic score to [0,1] safely
    sem_scores = (sem_sims - sem_sims.min()) / (sem_sims.max() - sem_sims.min() + 1e-9)

    for i, p in enumerate(places):
        d = haversine_m(user_lat, user_lng, p["lat"], p["lng"])
        dist_score = score_distance(d, radius_m)
        cat_score = score_category_match(p.get("categories", []), user_query)
        sem_score = float(sem_scores[i])

        user_boosts = user_boosts or {}
        cat_boost = 0.0
        for c in p.get("categories", []):
            cat_boost += user_boosts.get(c, 0.0)
        cat_boost = clamp(cat_boost, -0.10, 0.10)


        # Hybrid score: semantic + distance + small keyword boost
        score = 0.52 * sem_score + 0.33 * dist_score + 0.10 * cat_score + 0.05 * (cat_boost + 0.10)

        item = dict(p)
        item["distance_m"] = round(d, 1)
        item["semantic_score"] = round(sem_score, 4)
        item["score"] = round(score, 4)
        item["personal_boost"] = round(cat_boost, 4)
        ranked.append(item)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

