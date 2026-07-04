"""
UtilityLib FetchesDB — SQLite-based fetch store.

Replaces JSON file-based fetches from ~/Dev-Work-Local/Dashboard/*/fetches/
with a single indexed DB at ~/UtilityLib/fetches.db.

Usage:
    from UtilityLib.fetches_db import FetchesDB
    db = FetchesDB()

    # Store a fetch
    db.store(module="aws-vis", profile="default", regions=["us-east-1"], data={...})

    # Query
    rows = db.fetch(module="aws-vis", limit=10)
    rows = db.fetch_since(hours=2)

    # Cleanup
    db.cleanup(days=7)
"""

import os
import json
import sqlite3
import datetime
from typing import Any, Dict, List, Optional

FETCHES_DB = os.path.expanduser("~/.UtilityLib/fetches.db")


class FetchesDB:
    """SQLite fetch store — replaces JSON file fetches."""

    def __init__(self, db_path: str = FETCHES_DB):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _init_db(self):
        conn = self._connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fetches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                profile TEXT,
                regions TEXT,
                fetched_at TEXT NOT NULL,
                fetched_unix REAL,
                data TEXT NOT NULL,
                source_file TEXT,
                migrated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_module ON fetches(module)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_profile ON fetches(profile)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_fetched_at ON fetches(fetched_at)")
        conn.commit()

    def store(self, module: str, data: Dict, profile: str = None,
              regions: List[str] = None, fetched_at: str = None):
        """Store a fetch result."""
        now = datetime.datetime.now()
        if fetched_at is None:
            fetched_at = now.strftime("%Y%m%d%H%M%S")
        fetched_unix = now.timestamp()

        conn = self._connect()
        conn.execute(
            "INSERT INTO fetches (module, profile, regions, fetched_at, fetched_unix, data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (module, profile, ",".join(regions) if regions else None,
             fetched_at, fetched_unix, json.dumps(data, ensure_ascii=False))
        )
        conn.commit()

    def fetch(self, module: str = None, profile: str = None,
              limit: int = 20) -> List[Dict]:
        """Fetch records, optionally filtered."""
        conn = self._connect()
        query = "SELECT * FROM fetches WHERE 1=1"
        params = []

        if module:
            query += " AND module = ?"
            params.append(module)
        if profile:
            query += " AND profile = ?"
            params.append(profile)

        query += " ORDER BY fetched_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def fetch_since(self, hours: int = 24, module: str = None) -> List[Dict]:
        """Fetch records from last N hours."""
        conn = self._connect()
        cutoff = (datetime.datetime.now() - datetime.timedelta(hours=hours)).timestamp()

        query = "SELECT * FROM fetches WHERE fetched_unix > ?"
        params = [cutoff]

        if module:
            query += " AND module = ?"
            params.append(module)

        query += " ORDER BY fetched_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_data(self, row: Dict) -> Dict:
        """Parse JSON data from a fetch record."""
        try:
            return json.loads(row["data"])
        except (json.JSONDecodeError, TypeError):
            return {}

    def cleanup(self, days: int = 7) -> int:
        """Delete records older than N days."""
        conn = self._connect()
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).timestamp()
        cur = conn.execute("DELETE FROM fetches WHERE fetched_unix < ?", (cutoff,))
        conn.commit()
        deleted = cur.rowcount
        return deleted

    def stats(self) -> Dict:
        """Get summary statistics."""
        conn = self._connect()
        total = conn.execute("SELECT COUNT(*) as cnt FROM fetches").fetchone()["cnt"]
        modules = conn.execute(
            "SELECT module, COUNT(*) as cnt FROM fetches GROUP BY module ORDER BY cnt DESC"
        ).fetchall()
        latest = conn.execute("SELECT MAX(fetched_at) as latest FROM fetches").fetchone()["latest"]
        conn.close()
        return {
            "total": total,
            "modules": {r["module"]: r["cnt"] for r in modules},
            "latest_fetch": latest,
        }

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
