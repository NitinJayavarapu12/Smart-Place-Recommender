# 🧠 Smart Place Recommender

Hybrid recommendation system combining semantic embeddings, distance scoring, 
and feedback-driven personalization. Built with FastAPI, SentenceTransformers, 
SQLite, and OpenStreetMap.

Includes:
- Semantic ranking (MiniLM embeddings)
- Real-time distance scoring
- Feedback learning loop
- Caching + retry logic
- Interactive web UI with map



## 🎬 Demo

- Web UI: http://127.0.0.1:8000/
- API Docs: http://127.0.0.1:8000/docs



## 🏗 Architecture

User → FastAPI → Places Provider (Overpass)
     → Ranking Engine
        ├── Semantic Embeddings
        ├── Distance Scoring
        ├── Keyword Boost
        └── Personalization (SQLite)



## 🧠 Ranking Logic

score =
  0.52 * semantic_similarity +
  0.33 * distance_score +
  0.10 * keyword_match +
  0.05 * personalization_boost



## ⚡ Performance Optimizations

- Cached place embeddings by text hash
- Cached Overpass API responses (TTL 60s)
- Retry + fallback across multiple Overpass endpoints
- LRU-loaded embedding model
- Normalized semantic scoring



## ▶️ Run Locally

git clone ...
cd ...
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload

