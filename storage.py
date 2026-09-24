"""Простое SQLite-хранилище для веб-интерфейса: список конкурентов, снимки
подписчиков со временем, посты. Всё в одном файле recon.db рядом со скриптом."""
import sqlite3
import time
from datetime import datetime

DB_PATH = "recon.db"


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            niche TEXT NOT NULL DEFAULT '',
            added_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            taken_at TEXT NOT NULL,
            followers INTEGER
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            post_id TEXT NOT NULL,
            text TEXT,
            timestamp TEXT,
            permalink TEXT,
            likes INTEGER,
            views INTEGER,
            UNIQUE(competitor_id, post_id)
        );
        """
    )
    conn.commit()


def add_competitor(conn, username, niche):
    conn.execute(
        "INSERT INTO competitors (username, niche, added_at) VALUES (?, ?, ?)",
        (username, niche, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()


def delete_competitor(conn, competitor_id):
    conn.execute("DELETE FROM posts WHERE competitor_id=?", (competitor_id,))
    conn.execute("DELETE FROM snapshots WHERE competitor_id=?", (competitor_id,))
    conn.execute("DELETE FROM competitors WHERE id=?", (competitor_id,))
    conn.commit()


def save_snapshot(conn, competitor_id, followers, posts):
    conn.execute(
        "INSERT INTO snapshots (competitor_id, taken_at, followers) VALUES (?, ?, ?)",
        (competitor_id, datetime.now().isoformat(timespec="seconds"), followers),
    )
    for p in posts:
        conn.execute(
            """INSERT INTO posts (competitor_id, post_id, text, timestamp, permalink, likes, views)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(competitor_id, post_id) DO UPDATE SET
                   likes=excluded.likes, views=excluded.views""",
            (competitor_id, p["post_id"], p.get("text", ""),
             p.get("timestamp"), p.get("permalink"), p.get("likes", 0), p.get("views")),
        )
    conn.commit()


def list_competitors(conn):
    return conn.execute("SELECT * FROM competitors ORDER BY added_at").fetchall()


def latest_followers(conn, competitor_id):
    row = conn.execute(
        "SELECT followers FROM snapshots WHERE competitor_id=? ORDER BY taken_at DESC LIMIT 1",
        (competitor_id,),
    ).fetchone()
    return row["followers"] if row else None


def competitor_posts(conn, competitor_id):
    return conn.execute(
        "SELECT * FROM posts WHERE competitor_id=? ORDER BY timestamp DESC", (competitor_id,)
    ).fetchall()


def snapshot_count(conn, competitor_id):
    return conn.execute(
        "SELECT COUNT(*) c FROM snapshots WHERE competitor_id=?", (competitor_id,)
    ).fetchone()["c"]
