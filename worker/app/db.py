import os, psycopg2, json
from psycopg2.extras import Json

_conn = None
def get_conn():
    global _conn
    if _conn:
        return _conn
    _conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", 5432),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    _conn.autocommit = True
    return _conn

def insert_or_update_reel(meta: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO reels (platform, post_id, url, title, uploader, posted_time, video_s3_key, raw_metadata, status, error)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (url) DO UPDATE SET
          title = EXCLUDED.title,
          uploader = EXCLUDED.uploader,
          posted_time = EXCLUDED.posted_time,
          video_s3_key = EXCLUDED.video_s3_key,
          raw_metadata = EXCLUDED.raw_metadata,
          status = EXCLUDED.status,
          error = EXCLUDED.error
        """,
        (
            meta.get("platform", "facebook"),
            meta.get("post_id"),
            meta.get("url"),
            meta.get("title"),
            meta.get("uploader"),
            meta.get("posted_time"),
            meta.get("video_s3_key"),
            Json(meta.get("raw_metadata") or {}),
            meta.get("status", "fetched"),
            meta.get("error")
        )
    )
    cur.close()
