# Smart Place Recommender

Hybrid AI-powered nearby place recommender built with FastAPI.

This project combines semantic search (sentence embeddings), geographic ranking (Haversine distance), and user feedback personalization to generate intelligent place recommendations using OpenStreetMap data.

It is designed as a production-style backend project demonstrating:

- API design with FastAPI
- Hybrid ranking systems
- Embedding-based semantic matching
- Feedback-driven personalization
- Caching + retry strategies
- Clean modular architecture

---

## 🚀 Overview

The Smart Place Recommender is a lightweight recommendation system that:

1. Fetches nearby places from OpenStreetMap (Overpass API)
2. Converts user queries and place descriptions into embeddings
3. Ranks results using a hybrid scoring strategy
4. Learns from user feedback (like/dislike/click)
5. Returns personalized recommendations

Example query:

> "quiet coffee shop to work"

The system boosts cafes over restaurants, ranks closer locations higher, and increases scores over time based on user preferences.

---

## 🏗 Architecture

```
User (Web UI)
      │
      ▼
FastAPI Backend
      │
      ├── Web Layer (Jinja2 + Leaflet)
      ├── API Layer (/recommend, /feedback)
      ├── Ranking Engine
      │      ├── Embeddings (MiniLM)
      │      ├── Distance Scoring
      │      ├── Keyword Boost
      │      └── Personalization Boost
      │
      ├── Data Provider (Overpass API)
      │      ├── Retry + Backoff
      │      └── TTL Cache
      │
      └── SQLite DB (User Feedback)
```

---

## 🧠 How It Works

Final score is computed using:

score =
  0.52 * semantic_similarity +
  0.33 * distance_score +
  0.10 * keyword_match +
  0.05 * personalization_boost

Where:

- **Semantic Similarity** → Sentence embeddings (MiniLM)
- **Distance Score** → Haversine distance normalization
- **Keyword Boost** → Simple rule-based category boosts
- **Personalization Boost** → Learned from user feedback (SQLite)

---

## 🌐 How to Use

### Web UI

Open:

```
http://127.0.0.1:8000/
```

You can:

- Enter a query
- Adjust radius and result count
- See ranked results
- View map pins
- Like / Dislike places
- Re-run search to see personalization effects

---

### API Endpoints

#### Health Check

```
GET /health
```

#### Recommend Places

```
POST /recommend
```

Example request body:

```json
{
  "lat": 30.4213,
  "lng": -87.2169,
  "query": "coffee shop to work",
  "radius_m": 2000,
  "max_results": 5,
  "open_now": true,
  "user_id": "demo_user"
}
```

#### Submit Feedback

```
POST /feedback
```

```json
{
  "user_id": "demo_user",
  "place_id": "osm:node:123456",
  "action": "like",
  "category_hint": "amenity:cafe"
}
```

#### Clear Feedback

```
DELETE /feedback/{user_id}
```

## 🔥 Demo Flow (Personalization Example)

1. Search: `"coffee shop to work"`
2. Like multiple cafes
3. Search again
4. Observe:
   - `personal_boost` increases
   - Cafe scores increase
   - Restaurants drop in ranking

This demonstrates a real feedback learning loop.

---

## ⚡ Performance Optimizations

- Cached place embeddings by text hash
- Cached Overpass API responses (TTL 60s)
- Retry + fallback across multiple Overpass endpoints
- LRU-loaded embedding model
- Normalized semantic scoring

---

## 🗺️ Data Source

Data is retrieved from:

- **OpenStreetMap (Overpass API)**

Features:
- Retry + fallback endpoints
- 60-second TTL cache
- Automatic deduplication
- Basic category normalization

No paid APIs required.

---

## ▶️ Run Locally

- git clone ...
- cd ...
- python -m venv .venv
- pip install -r requirements.txt
- uvicorn app.main:app --reload

