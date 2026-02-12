from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.database import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    place_id = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)  # "like" | "dislike" | "click"
    category_hint = Column(String, nullable=True)  # e.g., "amenity:cafe"
    created_at = Column(DateTime, default=datetime.utcnow)
