import random
import time
import requests
from typing import List, Optional, Dict, Any, Tuple
from cachetools import TTLCache

# Multiple Overpass instances (fallbacks)
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Cache results for 60 seconds to avoid repeated calls
_cache = TTLCache(maxsize=256, ttl=60)

CATEGORY_TO_TAGS = {
    "coffee": [("amenity", "cafe")],
    "cafe": [("amenity", "cafe")],
    "restaurant": [("amenity", "restaurant")],
    "fast_food": [("amenity", "fast_food")],
    "park": [("leisure", "park")],
    "gym": [("leisure", "fitness_centre")],
    "bar": [("amenity", "bar")],
    "pharmacy": [("amenity", "pharmacy")],
    "hospital": [("amenity", "hospital")],
    "library": [("amenity", "library")],
    "supermarket": [("shop", "supermarket")],
}


def _make_overpass_query(lat: float, lng: float, radius_m: int, categories: List[str]) -> str:
    tag_filters: List[Tuple[str, str]] = []
    for c in categories:
        tag_filters.extend(CATEGORY_TO_TAGS.get(c.lower(), []))

    if not tag_filters:
        tag_filters = [("amenity", "cafe"), ("amenity", "restaurant"), ("leisure", "park")]

    parts = []
    for k, v in tag_filters:
        parts.append(f'node["{k}"="{v}"](around:{radius_m},{lat},{lng});')
        parts.append(f'way["{k}"="{v}"](around:{radius_m},{lat},{lng});')
        parts.append(f'relation["{k}"="{v}"](around:{radius_m},{lat},{lng});')

    return f"""
    [out:json][timeout:25];
    (
      {''.join(parts)}
    );
    out center tags;
    """


def fetch_places(
    lat: float,
    lng: float,
    radius_m: int,
    categories: Optional[List[str]] = None,
    open_now: bool = True,  # not supported reliably in OSM; kept for compatibility
    limit: int = 25,
) -> List[Dict[str, Any]]:
    categories = categories or ["cafe", "restaurant", "park"]

    cache_key = (round(lat, 4), round(lng, 4), int(radius_m), tuple(sorted([c.lower() for c in categories])), int(limit))
    if cache_key in _cache:
        return _cache[cache_key]

    query = _make_overpass_query(lat, lng, radius_m, categories)

    last_err = None
    urls = OVERPASS_URLS[:]
    random.shuffle(urls)

    # retry strategy: 3 attempts with small backoff
    for attempt in range(1, 4):
        for url in urls:
            try:
                resp = requests.post(url, data={"data": query}, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                places = normalize_places(data.get("elements", []))[:limit]
                _cache[cache_key] = places
                return places
            except requests.RequestException as e:
                last_err = e

        # backoff between attempts
        time.sleep(0.6 * attempt)

    # If all fail, raise a clean error
    raise RuntimeError(f"Overpass timed out/unavailable after retries. Last error: {last_err}")


def normalize_places(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []

    for el in elements:
        tags = el.get("tags", {}) or {}
        name = tags.get("name")
        if not name:
            continue

        if "lat" in el and "lon" in el:
            plat, plng = el["lat"], el["lon"]
        else:
            center = el.get("center") or {}
            plat, plng = center.get("lat"), center.get("lon")
            if plat is None or plng is None:
                continue

        categories = []
        for key in ("amenity", "shop", "leisure", "tourism"):
            if tags.get(key):
                categories.append(f"{key}:{tags[key]}")

        address_bits = [
            tags.get("addr:housenumber"),
            tags.get("addr:street"),
            tags.get("addr:city"),
            tags.get("addr:state"),
            tags.get("addr:postcode"),
        ]
        address = " ".join([b for b in address_bits if b])

        out.append(
            {
                "place_id": f"osm:{el.get('type')}:{el.get('id')}",
                "name": name,
                "address": address or None,
                "lat": float(plat),
                "lng": float(plng),
                "rating": None,
                "price_level": None,
                "is_open": None,
                "categories": categories,
            }
        )

    # Deduplicate
    seen = set()
    deduped = []
    for p in out:
        if p["place_id"] in seen:
            continue
        seen.add(p["place_id"])
        deduped.append(p)

    return deduped
