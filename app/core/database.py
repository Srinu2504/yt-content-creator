import sqlite3
import uuid
from app.core.config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS videos (
                id           TEXT PRIMARY KEY,
                youtube_url  TEXT UNIQUE NOT NULL,
                youtube_id   TEXT,
                title        TEXT,
                channel      TEXT,
                duration_sec INTEGER,
                transcript   TEXT,
                created_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS generated_content (
                id          TEXT PRIMARY KEY,
                video_id    TEXT NOT NULL REFERENCES videos(id),
                format      TEXT NOT NULL,
                content     TEXT NOT NULL,
                word_count  INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)


def save_video(youtube_url, youtube_id, title, channel, duration_sec, transcript):
    vid_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO videos
               (id, youtube_url, youtube_id, title, channel, duration_sec, transcript)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (vid_id, youtube_url, youtube_id, title, channel, duration_sec, transcript)
        )
    return vid_id


def get_video_by_url(url):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM videos WHERE youtube_url = ?", (url,)
        ).fetchone()


def get_all_videos():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM videos ORDER BY created_at DESC"
        ).fetchall()


def save_content(video_id, fmt, content):
    content_id = str(uuid.uuid4())
    word_count = len(content.split())
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO generated_content (id, video_id, format, content, word_count)
               VALUES (?, ?, ?, ?, ?)""",
            (content_id, video_id, fmt, content, word_count)
        )
    return content_id


def get_content_for_video(video_id):
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM generated_content
               WHERE video_id = ? ORDER BY created_at DESC""",
            (video_id,)
        ).fetchall()
    return {row["format"]: dict(row) for row in rows}


def delete_video(video_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM generated_content WHERE video_id = ?", (video_id,))
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
