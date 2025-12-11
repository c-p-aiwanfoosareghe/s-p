from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from app.scraper import scrape_reel
import os

app = FastAPI(title="Reels Scraper API")

# Mount videos folder at /videos
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True

@app.post("/scrape")
async def enqueue(req: ReelsRequest):
    try:
        result = await scrape_reel(str(req.url), prefer_proxy=req.prefer_proxy)
        video_key = result.get("video_s3_key")
        video_url = None
        if video_key:
            video_url = f"{os.getenv('BASE_URL', 'https://s-p-1.onrender.com')}/videos/{os.path.basename(video_key)}"
        return {
            "ok": True,
            "data": {
                "url": req.url,
                "proxy_used": req.prefer_proxy,
                "status": "Scraped successfully",
                "video_url": video_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"ok": True}
