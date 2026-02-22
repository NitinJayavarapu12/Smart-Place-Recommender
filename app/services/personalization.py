import sqlite3

DB_PATH = "feedback.db"


def init_db():
    """Create the feedback table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            place_id TEXT NOT NULL,
            action TEXT NOT NULL,
            category_hint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_id ON feedback(user_id)
    """)
    conn.commit()
    conn.close()


def save_feedback(user_id: str, place_id: str, action: str, category_hint: str | None):
    """Save a single feedback entry."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO feedback (user_id, place_id, action, category_hint) VALUES (?, ?, ?, ?)",
        (user_id, place_id, action, category_hint)
    )
    conn.commit()
    conn.close()


def get_user_profile(user_id: str) -> dict[str, float]:
    """
    Build a personalization profile from a user's feedback history.

    Returns a dict of category_hint -> boost score (0.0 to 1.0).
    Likes add +1.0, dislikes add -1.0, clicks add +0.3.
    Final scores are normalized to 0-1 range.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT action, category_hint FROM feedback WHERE user_id = ? AND category_hint IS NOT NULL",
        (user_id,)
    ).fetchall()
    conn.close()

    action_weights = {"like": 1.0, "dislike": -1.0, "click": 0.3}
    category_scores: dict[str, float] = {}

    for row in rows:
        cat = row["category_hint"]
        action = row["action"]
        category_scores[cat] = category_scores.get(cat, 0.0) + action_weights.get(action, 0.0)

    if not category_scores:
        return {}

    # Normalize so the highest score = 1.0
    max_val = max(abs(v) for v in category_scores.values()) or 1
    return {k: max(0.0, v / max_val) for k, v in category_scores.items()}


def clear_user_feedback(user_id: str):
    """Delete all feedback for a given user."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()