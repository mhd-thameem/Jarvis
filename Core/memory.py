import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "jarvis_memory.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Stores discrete facts, preferences, and recurring goals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        # Stores logs, routine updates, training notes, and chats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                category TEXT,
                entry TEXT
            )
        """)
        conn.commit()

def set_profile_fact(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO profile (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )

def get_all_facts() -> str:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT key, value FROM profile").fetchall()
        return "\n".join([f"- {r[0]}: {r[1]}" for r in rows]) if rows else "No profile data yet."

def log_event(category: str, entry: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO timeline (timestamp, category, entry) VALUES (?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), category, entry)
        )

def get_recent_history(limit: int = 5) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT timestamp, category, entry FROM timeline ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return "\n".join([f"[{r[0]}] [{r[1]}] {r[2]}" for r in reversed(rows)]) if rows else "No recent history."

# Initialize the tables on import
init_db()