# app/storage.py
import os

VIDEOS_DIR = "videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

def upload_bytes(key: str, data: bytes, content_type="video/mp4"):
    file_path = os.path.join(VIDEOS_DIR, os.path.basename(key))
    with open(file_path, "wb") as f:
        f.write(data)
    return file_path
