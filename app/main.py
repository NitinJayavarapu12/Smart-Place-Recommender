from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.database import engine, Base
from app.db import models  # noqa: F401

from app.api.routes import router, feedback_router
from app.web.pages import web_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Place Recommender",
    version="1.0.0",
    summary="Hybrid place recommendations (semantic + distance) with feedback personalization",
)

# Serve frontend assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(web_router)       # serves GET /
app.include_router(router)           # /health, /recommend
app.include_router(feedback_router)  # /feedback
