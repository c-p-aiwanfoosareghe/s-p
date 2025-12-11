import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from yt_dlp import YoutubeDL

from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

VIDEOS_DIR = "videos"
os.makedirs(VIDEOS_DIR, exist_ok=True)

class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True  # still there if you want

def download_reel(url: str):
    """
    Downloads Facebook reel using yt-dlp and returns local video path.
    """
    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(VIDEOS_DIR, "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"{info['id']}.mp4"
        return f"/videos/{filename}"  # URL served by FastAPI

@app.post("/scrape")
def scrape(req: ReelsRequest):
    try:
        video_url = download_reel(str(req.url))  # <--- cast to str
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
        
# Serve downloaded videos
from fastapi.staticfiles import StaticFiles
app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
