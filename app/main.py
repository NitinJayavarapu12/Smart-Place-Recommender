from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.services.personalization import init_db
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup
    init_db()
    yield
    # Runs once on shutdown (nothing needed)


app = FastAPI(
    title="Smart Place Recommender",
    version="2.0.0",
    description="""
## Smart Place Recommender API

A hybrid AI-powered place recommendation engine built on top of **OpenStreetMap**.

### How scoring works

Each place is scored using a weighted combination of four signals:

| Signal | Default Weight | Description |
|---|---|---|
| Semantic Similarity | 52% | Sentence embedding cosine similarity between query and place |
| Distance Score | 33% | Exponential decay based on Haversine distance |
| Keyword Match | 10% | Rule-based category boost from query keywords |
| Personalization | 5% | Learned boost from user like/dislike/click history |

> **Dynamic Weights**: Weights shift automatically based on query intent.
> Queries like *"nearest pharmacy"* increase distance weight to 55%.
> Queries like *"cozy romantic spot"* increase semantic weight to 65%.

### No paid APIs required
All place data comes from OpenStreetMap via the Overpass API.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Serve static files (our UI)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Register all API routes under /api/v1
app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def serve_ui():
    return FileResponse("static/index.html")