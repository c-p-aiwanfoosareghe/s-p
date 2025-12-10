import os

# Dummy storage for Option B
S3_BUCKET = os.getenv("S3_BUCKET", "local")

def upload_bytes(key: str, data: bytes, content_type: str = "video/mp4"):
    """
    In Option B, we simply save video to local folder `videos/` instead of S3.
    """
    os.makedirs("videos", exist_ok=True)
    filepath = os.path.join("videos", key.replace("/", "_"))
    with open(filepath, "wb") as f:
        f.write(data)
    return filepath

# Dummy client placeholder
_client = None
