import httpx
import hashlib
from cachetools import TTLCache

# TTL cache: max 256 entries, 60s TTL
_cache: TTLCache = TTLCache(maxsize=256, ttl=60)

# Overpass endpoints (tried in order if one fails)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# OSM tag normalization
CATEGORY_MAP = {
    "cafe": "Cafe",
    "restaurant": "Restaurant",
    "fast_food": "Fast Food",
    "bar": "Bar",
    "pub": "Pub",
    "pharmacy": "Pharmacy",
    "hospital": "Hospital",
    "clinic": "Clinic",
    "doctors": "Doctor",
    "dentist": "Dentist",
    "supermarket": "Supermarket",
    "convenience": "Convenience Store",
    "bakery": "Bakery",
    "library": "Library",
    "park": "Park",
    "gym": "Gym",
    "fitness_centre": "Gym",
    "hotel": "Hotel",
    "hostel": "Hostel",
    "museum": "Museum",
    "cinema": "Cinema",
    "theatre": "Theatre",
    "bank": "Bank",
    "atm": "ATM",
    "fuel": "Gas Station",
    "parking": "Parking",
    "school": "School",
    "university": "University",
    "college": "College",
    "place_of_worship": "Place of Worship",
    "post_office": "Post Office",
    "marketplace": "Market",
    "food_court": "Food Court",
    "ice_cream": "Ice Cream",
    "juice_bar": "Juice Bar",
}


def _cache_key(lat: float, lng: float, radius_m: int) -> str:
    raw = f"{lat:.4f}:{lng:.4f}:{radius_m}"
    return hashlib.md5(raw.encode()).hexdigest()


def _build_query(lat: float, lng: float, radius_m: int) -> str:
    return f"""
    [out:json][timeout:20];
    (
      node["amenity"](around:{radius_m},{lat},{lng});
      node["shop"](around:{radius_m},{lat},{lng});
      node["tourism"](around:{radius_m},{lat},{lng});
      node["leisure"](around:{radius_m},{lat},{lng});
    );
    out body;
    """


def _normalize_element(el: dict) -> dict | None:
    tags = el.get("tags", {})
    name = tags.get("name") or tags.get("name:en")
    if not name:
        return None

    for key in ("amenity", "shop", "tourism", "leisure"):
        if key in tags:
            raw_cat = tags[key]
            category = CATEGORY_MAP.get(raw_cat, raw_cat.replace("_", " ").title())
            category_hint = f"{key}:{raw_cat}"
            break
    else:
        return None

    return {
        "place_id": f"osm:{el['type']}:{el['id']}",
        "name": name,
        "category": category,
        "category_hint": category_hint,
        "lat": el["lat"],
        "lng": el["lon"],
        "tags": {k: v for k, v in tags.items() if k != "name"},
    }


async def fetch_places(lat: float, lng: float, radius_m: int) -> list[dict]:
    key = _cache_key(lat, lng, radius_m)
    if key in _cache:
        return _cache[key]

    query = _build_query(lat, lng, radius_m)
    last_error = None

    async with httpx.AsyncClient(timeout=25) as client:
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                resp = await client.post(endpoint, data={"data": query})
                resp.raise_for_status()
                data = resp.json()
                elements = data.get("elements", [])

                seen = set()
                results = []
                for el in elements:
                    place = _normalize_element(el)
                    if place and place["place_id"] not in seen:
                        seen.add(place["place_id"])
                        results.append(place)

                _cache[key] = results
                return results

            except Exception as e:
                last_error = e
                continue

    raise RuntimeError(f"All Overpass endpoints failed. Last error: {last_error}")