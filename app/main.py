import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from yt_dlp import YoutubeDL
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------
# Create FastAPI app
# ---------------------------------------------------------
app = FastAPI()

# ---------------------------------------------------------
# Directories
# ---------------------------------------------------------
VIDEOS_DIR = "videos"
FRONTEND_DIR = "frontend"

os.makedirs(VIDEOS_DIR, exist_ok=True)

# ---------------------------------------------------------
# Serve Frontend & Videos
# ---------------------------------------------------------
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")

# ---------------------------------------------------------
# Request Model
# ---------------------------------------------------------
class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True  # optional compatibility

# ---------------------------------------------------------
# reel downloader using yt-dlp
# ---------------------------------------------------------
def download_reel(url: str):
    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(VIDEOS_DIR, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"{info['id']}.mp4"
        return f"/videos/{filename}"

# ---------------------------------------------------------
# API route
# ---------------------------------------------------------
@app.post("/scrape")
def scrape(req: ReelsRequest):
    try:
        video_url = download_reel(str(req.url))
        return {
            "ok": True,
            "data": {
                "url": str(req.url),
                "proxy_used": False,
                "status": "Scraped successfully",
                "video_url": video_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
