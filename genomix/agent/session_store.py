"""Session history storage with SQLite + FTS5."""
import json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionStore:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, title TEXT, messages TEXT, created_at TEXT)")
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(id, title, content)")

    def save_session(self, messages, title=""):
        sid = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        content = " ".join(m.get("content", "") or "" for m in messages)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO sessions VALUES (?,?,?,?)", (sid, title, json.dumps(messages), now))
            conn.execute("INSERT INTO sessions_fts VALUES (?,?,?)", (sid, title, content))
        return sid

    def load_session(self, session_id):
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT messages FROM sessions WHERE id=?", (session_id,)).fetchone()
        return json.loads(row[0]) if row else []

    def search(self, query):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, title FROM sessions_fts WHERE sessions_fts MATCH ?", (query,)).fetchall()
        return [{"id": r[0], "title": r[1]} for r in rows]

    def list_sessions(self, limit=20):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]
