from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from app.scraper import scrape_reel
import os

# ensure videos folder exists
os.makedirs("videos", exist_ok=True)

app = FastAPI(title="Reels Scraper API")

# Mount /videos for serving video files
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True

@app.post("/scrape")
async def scrape(req: ReelsRequest):
    try:
        result = await scrape_reel(req.url, req.prefer_proxy)
        video_key = result.get("video_s3_key")
        video_url = f"https://s-p-1.onrender.com/videos/{os.path.basename(video_key)}" if video_key else None
        return {
            "ok": True,
            "data": {
                "url": req.url,
                "status": result.get("status"),
                "video_url": video_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"ok": True}
