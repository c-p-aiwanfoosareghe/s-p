import os
from celery import Celery
from celery.schedules import crontab
import asyncio

os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")  # avoids some celery/playwright issues

app = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

# optional scheduled beat entries (example)
app.conf.beat_schedule = {
    # example: run a scheduled job
    # 'example-every-hour': {
    #     'task': 'worker.app.tasks.scheduled_enqueue',
    #     'schedule': crontab(minute=0, hour='*/1'),
    #     'args': ('https://www.facebook.com/.../reel/123',)
    # },
}

@app.task(bind=True, name="worker.app.tasks.enqueue_reel")
def enqueue_reel(self, url: str, prefer_proxy: bool = True):
    """
    Synchronous Celery wrapper that runs the async scraper.
    Returns serialized result or raises.
    """
    from app.scraper import scrape_reel
    try:
        result = asyncio.run(scrape_reel(url, prefer_proxy=prefer_proxy))
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.task(name="worker.app.tasks.scheduled_enqueue")
def scheduled_enqueue(url: str):
    return enqueue_reel.delay(url)
