import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from worker.app.tasks import enqueue_reel

app = FastAPI(title="Reels Scraper API")

class ReelsRequest(BaseModel):
    url: HttpUrl
    prefer_proxy: bool = True

@app.post("/scrape")
def enqueue(req: ReelsRequest):
    # enqueue Celery task
    try:
        task = enqueue_reel.delay(str(req.url), req.prefer_proxy)
        return {"ok": True, "task_id": task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"ok": True}
