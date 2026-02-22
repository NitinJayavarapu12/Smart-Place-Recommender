import math
import re
from app.services.embedder import embed, embed_batch, cosine_similarity

# ── Query Intent Detection ───────────────────────────────────────────────────

# These patterns mean the user wants the CLOSEST place
DISTANCE_PRIORITY_PATTERNS = [
    r"\b(nearest|closest|nearby|near me|walking distance|quick|fast)\b",
    r"\b(pharmacy|hospital|clinic|atm|bank|gas station|fuel|parking)\b",
]

# These patterns mean the user cares more about VIBE/FEEL
SEMANTIC_PRIORITY_PATTERNS = [
    r"\b(vibe|feel|atmosphere|cozy|quiet|lively|romantic|trendy|hip|aesthetic)\b",
    r"\b(good for|place to|spot to|somewhere to)\b",
]

# Keyword → category boosts
KEYWORD_BOOSTS: dict[str, list[str]] = {
    "coffee": ["amenity:cafe"],
    "cafe": ["amenity:cafe"],
    "work": ["amenity:cafe", "amenity:library"],
    "study": ["amenity:cafe", "amenity:library"],
    "eat": ["amenity:restaurant", "amenity:fast_food", "amenity:food_court", "amenity:cafe"],
    "food": ["amenity:restaurant", "amenity:fast_food", "amenity:food_court", "amenity:cafe"],
    "lunch": ["amenity:restaurant", "amenity:fast_food", "amenity:food_court", "amenity:cafe"],
    "dinner": ["amenity:restaurant", "amenity:bar", "amenity:pub"],
    "breakfast": ["amenity:cafe", "amenity:bakery", "amenity:restaurant"],
    "brunch": ["amenity:cafe", "amenity:restaurant"],
    "friends": ["amenity:restaurant", "amenity:bar", "amenity:pub", "amenity:cafe", "amenity:food_court"],
    "hangout": ["amenity:restaurant", "amenity:bar", "amenity:pub", "amenity:cafe"],
    "eat out": ["amenity:restaurant", "amenity:fast_food", "amenity:food_court"],
    "beer": ["amenity:bar", "amenity:pub"],
    "drink": ["amenity:bar", "amenity:pub", "amenity:cafe"],
    "park": ["leisure:park"],
    "gym": ["leisure:fitness_centre", "amenity:gym"],
    "workout": ["leisure:fitness_centre", "amenity:gym"],
    "book": ["amenity:library"],
    "shop": ["shop:supermarket", "shop:convenience"],
    "grocery": ["shop:supermarket"],
    "pharmacy": ["amenity:pharmacy"],
    "medicine": ["amenity:pharmacy"],
    "doctor": ["amenity:doctors", "amenity:clinic"],
    "hospital": ["amenity:hospital"],
    "hotel": ["tourism:hotel"],
    "stay": ["tourism:hotel", "tourism:hostel"],
    "museum": ["tourism:museum"],
    "movie": ["amenity:cinema"],
    "film": ["amenity:cinema"],
    "art": ["tourism:museum"],
}

# Categories to penalize for certain query types
# If query contains the key, these category_hints get a score penalty
CATEGORY_PENALTIES: dict[str, list[str]] = {
    "lunch":     ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "dinner":    ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "breakfast": ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "brunch":    ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "eat":       ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "food":      ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "friends":   ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "coffee":    ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "drink":     ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "hangout":   ["amenity:place_of_worship", "amenity:school", "amenity:university", "amenity:college", "amenity:parking", "amenity:fuel"],
    "gym":       ["amenity:place_of_worship", "amenity:school", "amenity:parking", "amenity:fuel"],
    "workout":   ["amenity:place_of_worship", "amenity:school", "amenity:parking", "amenity:fuel"],
}

# Default scoring weights
DEFAULT_WEIGHTS = {
    "semantic": 0.52,
    "distance": 0.33,
    "keyword": 0.10,
    "personal": 0.05,
}


def detect_weights(query: str) -> dict[str, float]:
    """Shift weights based on what the query is asking for."""
    q = query.lower()
    distance_signal = any(re.search(p, q) for p in DISTANCE_PRIORITY_PATTERNS)
    semantic_signal = any(re.search(p, q) for p in SEMANTIC_PRIORITY_PATTERNS)

    if distance_signal and not semantic_signal:
        # e.g. "nearest pharmacy" → distance matters most
        return {"semantic": 0.30, "distance": 0.55, "keyword": 0.10, "personal": 0.05}
    elif semantic_signal and not distance_signal:
        # e.g. "cozy romantic atmosphere" → semantics matter most
        return {"semantic": 0.65, "distance": 0.20, "keyword": 0.10, "personal": 0.05}
    else:
        return DEFAULT_WEIGHTS


def keyword_score(query: str, category_hint: str) -> float:
    """Returns boost score. Positive if category matches query, negative if penalized."""
    q = query.lower()

    # Check penalties first
    for kw, hints in CATEGORY_PENALTIES.items():
        if kw in q and category_hint in hints:
            return -1.0  # Strong penalty

    # Check boosts
    for kw, hints in KEYWORD_BOOSTS.items():
        if kw in q and category_hint in hints:
            return 1.0

    return 0.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in meters between two lat/lng points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def distance_score(distance_m: float, radius_m: float) -> float:
    """Exponential decay: closer places score higher."""
    return math.exp(-3 * distance_m / radius_m)


def place_text(place: dict) -> str:
    """Build a rich text description of a place for embedding."""
    tags = place.get("tags", {})
    parts = [place["name"], place["category"]]
    for tag_key in ("cuisine", "sport", "description", "opening_hours"):
        if tag_key in tags:
            parts.append(tags[tag_key])
    return " ".join(parts)


def rank_places(
    query: str,
    user_lat: float,
    user_lng: float,
    radius_m: int,
    places: list[dict],
    user_profile: dict[str, float],
    max_results: int,
) -> list[dict]:
    if not places:
        return []

    weights = detect_weights(query)
    query_vec = embed(query)

    # Embed all place descriptions in one batch (much faster)
    texts = [place_text(p) for p in places]
    place_vecs = embed_batch(texts)

    scored = []
    for place, vec in zip(places, place_vecs):
        dist_m = haversine_m(user_lat, user_lng, place["lat"], place["lng"])

        sem   = cosine_similarity(query_vec, vec)
        dist  = distance_score(dist_m, radius_m)
        kw    = keyword_score(query, place.get("category_hint", ""))
        personal = user_profile.get(place.get("category_hint", ""), 0.0)

        final = (
            weights["semantic"]  * sem +
            weights["distance"]  * dist +
            weights["keyword"]   * kw +
            weights["personal"]  * personal
        )

        scored.append({
            **place,
            "distance_m": round(dist_m, 1),
            "score": {
                "semantic":        round(sem, 4),
                "distance":        round(dist, 4),
                "keyword":         round(kw, 4),
                "personalization": round(personal, 4),
                "final":           round(final, 4),
            },
        })

    scored.sort(key=lambda x: x["score"]["final"], reverse=True)
    return scored[:max_results]