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
                video_id    TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
                format      TEXT NOT NULL,
                content     TEXT NOT NULL,
                word_count  INTEGER,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_content_video_id
            ON generated_content(video_id);
        """)


def save_video(youtube_url, youtube_id, title, channel, duration_sec, transcript):
    with get_conn() as conn:
        # Check if video already exists — reuse same id
        existing = conn.execute(
            "SELECT id FROM videos WHERE youtube_url = ?", (youtube_url,)
        ).fetchone()

        if existing:
            vid_id = existing["id"]
            conn.execute(
                """UPDATE videos SET
                   youtube_id=?, title=?, channel=?, duration_sec=?, transcript=?
                   WHERE id=?""",
                (youtube_id, title, channel, duration_sec, transcript, vid_id)
            )
        else:
            vid_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO videos
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
        # Delete old entry for same format to avoid duplicates
        conn.execute(
            "DELETE FROM generated_content WHERE video_id=? AND format=?",
            (video_id, fmt)
        )
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
    # Keep newest entry per format
    seen = {}
    for row in rows:
        fmt = row["format"]
        if fmt not in seen:
            seen[fmt] = dict(row)
    return seen


def delete_video(video_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
