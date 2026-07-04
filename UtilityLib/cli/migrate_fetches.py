"""
migrate_fetches.py — one-time migration from JSON fetch files to SQLite.

Reads all fetch_*.json files from ~/Dev-Work-Local/D0015.../Dashboard/*/fetches/
Inserts into ~/UtilityLib/fetches.db
"""

import os
import json
import sqlite3
import datetime
import glob

DASHBOARD_BASE = os.path.expanduser("~/Dev-Work-Local/D0015--EIQdigitaL-NextEraAI/Dashboard")
FETCHES_DB = os.path.expanduser("~/.UtilityLib/fetches.db")


def init_db():
    conn = sqlite3.connect(FETCHES_DB)
    conn.execute("PRAGMA journal_mode=WAL")
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
            migrated_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_module ON fetches(module)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_profile ON fetches(profile)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_fetch_fetched_at ON fetches(fetched_at)")
    conn.commit()
    return conn


def parse_fetch_filename(filename):
    """Parse fetch_YYYYMMDD_HHMMSS_module_profile_region.json."""
    base = os.path.basename(filename).replace(".json", "")
    parts = base.split("_")
    # Expected: fetch_YYYYMMDD_HHMMSS_module_profile_region
    result = {"fetched_at": None, "module": None, "profile": None, "region": None}
    if len(parts) >= 2 and parts[0] == "fetch":
        result["fetched_at"] = parts[1]  # YYYYMMDD
        if len(parts) >= 3:
            result["fetched_at"] += parts[2]  # HHMMSS
        if len(parts) >= 4:
            result["module"] = parts[3]
        if len(parts) >= 5:
            result["profile"] = parts[4]
        if len(parts) >= 6:
            result["region"] = parts[5]
    return result


def migrate():
    conn = init_db()

    # Find all fetch files
    pattern = os.path.join(DASHBOARD_BASE, "*", "fetches", "fetch_*.json")
    files = sorted(glob.glob(pattern))
    print(f"Found {len(files)} fetch files")

    if not files:
        print("No files to migrate.")
        return

    # Check existing to avoid duplicates
    existing = conn.execute("SELECT COUNT(*) FROM fetches").fetchone()[0]
    print(f"Existing DB rows: {existing}")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    migrated = 0
    skipped = 0

    for filepath in files:
        with open(filepath) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                skipped += 1
                continue

        # Parse filename for metadata
        fn_meta = parse_fetch_filename(filepath)

        # Extract metadata from JSON content
        fetched_at = data.get("_fetched_at", fn_meta["fetched_at"])
        fetched_unix = data.get("_fetched_unix")
        profile = data.get("_profile", fn_meta["profile"])
        regions = data.get("_regions", fn_meta["region"])

        # Derive module from directory name
        module = filepath.split("/")[-3]  # e.g., "aws-vis"
        if module == "fetches":
            module = fn_meta["module"] or "unknown"

        # Store the full JSON as the data payload
        data_json = json.dumps(data, ensure_ascii=False)

        # Check for duplicate
        dup = conn.execute(
            "SELECT id FROM fetches WHERE module=? AND fetched_at=? AND profile=?",
            (module, fetched_at, profile)
        ).fetchone()

        if dup:
            skipped += 1
            continue

        regions_str = ",".join(regions) if regions else None
        conn.execute(
            "INSERT INTO fetches (module, profile, regions, fetched_at, fetched_unix, data, source_file, migrated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (module, profile, regions_str, fetched_at, fetched_unix, data_json, filepath, now)
        )
        migrated += 1

    conn.commit()

    # Verify
    total = conn.execute("SELECT COUNT(*) FROM fetches").fetchone()[0]
    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped: {skipped}")
    print(f"  Total in DB: {total}")

    # Show sample
    sample = conn.execute(
        "SELECT module, profile, fetched_at FROM fetches ORDER BY id DESC LIMIT 5"
    ).fetchall()
    print(f"\nLatest entries:")
    for s in sample:
        print(f"  {s[0]} | {s[1]} | {s[2]}")

    conn.close()


if __name__ == "__main__":
    migrate()
