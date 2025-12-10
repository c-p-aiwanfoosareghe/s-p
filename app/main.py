from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import traceback

app = FastAPI(title="Reels Scraper API")

# ---- Request Schema ----
class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True


# ---- Your scraping logic goes here ----
def scrape_reel(url: str, prefer_proxy: bool):
    """
    Put your actual scraping code here.
    This function should return the scraped result.
    """
    try:
        # Example (replace this with your real Instagram scraping logic):
        result = {
            "url": url,
            "proxy_used": prefer_proxy,
            "status": "Scraped successfully",
            # You can add downloaded video URL, caption, image, etc.
        }
        return result

    except Exception as e:
        print("Scraper Error:", traceback.format_exc())
        raise


# ---- API Endpoint ----
@app.post("/scrape")
def scrape(req: ReelsRequest):
    """
    Runs scraping immediately and returns the result directly.
    """
    try:
        data = scrape_reel(str(req.url), req.prefer_proxy)
        return {"ok": True, "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---- Health Check ----
@app.get("/health")
def health():
    return {"ok": True}
