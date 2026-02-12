from collections import Counter
from typing import Dict
from sqlalchemy.orm import Session
from app.db.models import Feedback

def get_user_category_boosts(db: Session, user_id: str, limit: int = 50) -> Dict[str, float]:
    rows = (
        db.query(Feedback)
        .filter(Feedback.user_id == user_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .all()
    )

    likes = Counter()
    dislikes = Counter()

    for r in rows:
        if not r.category_hint:
            continue
        if r.action == "like" or r.action == "click":
            likes[r.category_hint] += 1
        elif r.action == "dislike":
            dislikes[r.category_hint] += 1

    boosts = {}
    for cat, c in likes.items():
        boosts[cat] = boosts.get(cat, 0.0) + min(0.10, 0.02 * c)  # cap boost
    for cat, c in dislikes.items():
        boosts[cat] = boosts.get(cat, 0.0) - min(0.10, 0.02 * c)  # cap penalty

    return boosts
