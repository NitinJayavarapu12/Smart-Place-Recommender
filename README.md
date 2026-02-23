# Smart Place Recommender v2

> A hybrid AI-powered place recommendation engine built on **OpenStreetMap**. Type a natural language query like *"quiet coffee shop to work"* or *"lunch with friends"*, enter a city name, and get back intelligently ranked nearby places — no paid APIs required.

> 🚀 **[Live Demo → smart-place-recommender.onrender.com](https://smart-place-recommender.onrender.com)**

---

## Demo

![Smart Place Recommender UI](https://smart-place-recommender.onrender.com)

**Try these queries:**
- `"quiet coffee shop to work"` in New York, NY
- `"lunch with friends"` in London, UK
- `"nearest pharmacy"` in Tokyo, Japan
- `"cozy romantic dinner spot"` in Paris, France

---

## How It Works

Each place is scored using a **weighted combination of four signals**:

| Signal | Default Weight | Description |
|---|---|---|
| Semantic Similarity | **52%** | Cosine similarity between MiniLM sentence embeddings of the query and place |
| Distance Score | **33%** | Exponential decay based on Haversine distance from user location |
| Keyword Match | **10%** | Rule-based category boost from query keywords |
| Personalization | **5%** | Learned from user like / dislike / click history (SQLite) |

### Dynamic Weight Shifting

Weights shift automatically based on detected **query intent**:

| Query Type | Example | Behavior |
|---|---|---|
| Distance-priority | `"nearest pharmacy"` | Distance weight → **55%**, Semantic → 30% |
| Semantic-priority | `"cozy romantic atmosphere"` | Semantic weight → **65%**, Distance → 20% |
| Balanced | `"coffee shop to work"` | Default weights apply |

### Category Penalties

Irrelevant categories are actively penalized for certain queries. For example, searching *"lunch with friends"* will suppress churches, schools, parking lots, and gas stations from results — even if their embeddings are semantically close.

---

## Features

- 🔍 **Natural language search** — describe what you want, not just a category
- 📍 **Location by city name** — type "Tokyo" instead of coordinates; click map to set location
- 🧠 **AI semantic matching** — MiniLM sentence embeddings understand context and vibe
- 📏 **Smart distance scoring** — closer places ranked higher with exponential decay
- 🎯 **Keyword boosting** — food queries boost restaurants/cafes, gym queries boost fitness centers
- 🚫 **Category penalties** — food queries suppress churches, schools, parking lots
- 👍 **Personalization** — like/dislike places to influence future results
- 🗺️ **Interactive map** — color-coded markers (green = high score, orange = medium, red = lower)
- 📊 **Score breakdown** — see exactly why each place was ranked where it was
- ⚡ **Caching** — Overpass API responses cached 60s, embeddings cached in LRU cache
- 🔄 **Retry logic** — falls back across 3 Overpass endpoints if one fails
- 📖 **Auto API docs** — full interactive docs at `/docs` and `/redoc`

---

## API Endpoints

All endpoints are under `/api/v1`.

### `GET /api/v1/health`
Returns service status and model info.

**Response:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "embedding_model": "all-MiniLM-L6-v2"
}
```

---

### `POST /api/v1/recommend`
Get ranked place recommendations for a location and query.

**Request:**
```json
{
  "lat": 40.7128,
  "lng": -74.0060,
  "query": "quiet coffee shop to work",
  "radius_m": 1500,
  "max_results": 10,
  "open_now": false,
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "query": "quiet coffee shop to work",
  "total_fetched": 312,
  "total_returned": 10,
  "results": [
    {
      "place_id": "osm:node:123456",
      "name": "Blue Bottle Coffee",
      "category": "Cafe",
      "lat": 40.7142,
      "lng": -74.0035,
      "distance_m": 187.3,
      "tags": { "amenity": "cafe", "cuisine": "coffee_shop" },
      "score": {
        "semantic": 0.8421,
        "distance": 0.7102,
        "keyword": 1.0,
        "personalization": 0.0,
        "final": 0.6934
      }
    }
  ]
}
```

---

### `POST /api/v1/feedback`
Submit a like, dislike, or click to personalize future recommendations.

**Request:**
```json
{
  "user_id": "user_123",
  "place_id": "osm:node:123456",
  "action": "like",
  "category_hint": "amenity:cafe"
}
```

Actions: `like` · `dislike` · `click`

---

### `DELETE /api/v1/feedback/{user_id}`
Clear all personalization history for a user.

---

## Architecture

```
User (Browser)
      │
      ▼
FastAPI (app/main.py)
      │
      ├── Static UI  (static/index.html)
      │     ├── Leaflet.js map
      │     ├── Nominatim geocoding (city name → lat/lng)
      │     ├── Score breakdown bars per result
      │     └── Like / Dislike / Visit feedback buttons
      │
      └── /api/v1/ (app/api/routes.py)
              │
              ├── Ranking Engine (app/services/ranker.py)
              │     ├── Query Intent Detection → Dynamic Weights
              │     ├── Sentence Embeddings   (MiniLM, batch + LRU cache)
              │     ├── Haversine Distance Score
              │     ├── Keyword Category Boost
              │     ├── Category Penalties
              │     └── Personalization Boost
              │
              ├── Overpass Provider (app/services/places_provider.py)
              │     ├── Multi-endpoint Retry + Fallback
              │     └── TTL Cache (60s)
              │
              └── Personalization (app/services/personalization.py)
                    └── SQLite (feedback.db)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI |
| AI / Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Place data | OpenStreetMap via Overpass API |
| Geocoding | Nominatim (OpenStreetMap) |
| Feedback storage | SQLite |
| Frontend map | Leaflet.js |
| Caching | cachetools (LRU + TTL) |
| HTTP client | httpx |
| Hosting | Render (free tier) |

---

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/NitinJayavarapu12/Smart-Place-Recommender.git
cd Smart-Place-Recommender

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn app.main:app --reload
```

Then open:
- **UI** → `http://localhost:8000`
- **API Docs** → `http://localhost:8000/docs`
- **ReDoc** → `http://localhost:8000/redoc`

---

## Project Structure

```
Smart-Place-Recommender/
├── app/
│   ├── api/
│   │   ├── routes.py          # API endpoint definitions
│   │   └── schemas.py         # Request / response Pydantic models
│   ├── services/
│   │   ├── ranker.py          # Hybrid scoring engine + dynamic weights
│   │   ├── embedder.py        # MiniLM embeddings with LRU cache
│   │   ├── places_provider.py # Overpass API fetcher + TTL cache
│   │   └── personalization.py # SQLite feedback store
│   └── main.py                # FastAPI app entry point
├── static/
│   └── index.html             # Single-page UI (Leaflet map + search)
├── requirements.txt
├── render.yaml                # Render deployment config
└── README.md
```

---

## Personalization Demo

1. Search `"coffee shop to work"` in your city
2. **Like** several cafes in the results
3. Search again
4. Notice `personalization` score increases for cafes
5. Cafes rank higher, other categories drop

This demonstrates a real feedback learning loop without any ML model training — just lightweight SQLite-backed preference tracking.

---

## Design Decisions

**Why OpenStreetMap over Google Places?**
No API key, no billing, no rate limit surprises. OSM has excellent global coverage and is completely free.

**Why MiniLM over larger models?**
It's fast enough to run on a free Render instance, fits in memory, and performs well for short semantic queries. A larger model would improve accuracy but kill cold-start time.

**Why SQLite over a full database?**
This is a portfolio project. SQLite is zero-config, file-based, and sufficient for demonstrating personalization concepts without infrastructure overhead.

**Why dynamic weights instead of a fixed formula?**
Real-world queries have different intents. "Nearest ATM" and "cozy romantic dinner" should not use the same scoring weights — one is purely proximity-driven, the other is vibe-driven.

---
