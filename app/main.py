from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from app.scraper import scrape_reel

app = FastAPI(title="Reels Scraper API")

class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True

@app.post("/scrape")
async def scrape(req: ReelsRequest):
    try:
        # scrape the reel
        result = await scrape_reel(req.url, req.prefer_proxy)

        # determine downloadable URL
        video_s3_key = result.get("video_s3_key")
        if video_s3_key:
            # assuming your server serves /videos/<key> at root
            download_url = f"{req.url.scheme}://{req.url.netloc}/{video_s3_key}" \
                if video_s3_key.startswith("http") is False else video_s3_key
        else:
            download_url = None

        return {
            "ok": True,
            "data": {
                "url": req.url,
                "status": result.get("status"),
                "video_url": download_url
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"ok": True}
