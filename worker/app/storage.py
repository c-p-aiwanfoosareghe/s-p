import os
from minio import Minio
from urllib.parse import urlparse

S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_USE_SSL = os.getenv("S3_USE_SSL", "false").lower() == "true"
S3_REGION = os.getenv("S3_REGION", "us-east-1")

_client = Minio(
    endpoint=S3_ENDPOINT,
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=S3_USE_SSL,
)

def ensure_bucket():
    if not _client.bucket_exists(S3_BUCKET):
        _client.make_bucket(S3_BUCKET, location=S3_REGION)

def upload_bytes(key: str, data: bytes, content_type="application/octet-stream"):
    ensure_bucket()
    _client.put_object(S3_BUCKET, key, data=io.BytesIO(data), length=len(data), content_type=content_type)
    return key
