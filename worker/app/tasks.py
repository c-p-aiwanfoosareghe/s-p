import os
from celery import Celery
from app.scraper import scrape_reel

app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

app.conf.beat_schedule = {
    # an example scheduled task (disabled by default)
    # 'sample-schedule': {
    #     'task': 'app.tasks.scheduled_fetch',
    #     'schedule': 60.0,
    #     'args': ('https://www.facebook.com/.../reel/123',)
    # },
}

@app.task(bind=True, name="app.tasks.enqueue_reel")
def enqueue_reel(self, url, prefer_proxy=True):
    """
    Enqueue a reel scrape job. This wrapper synchronously runs the async scraper
    because Celery workers are synchronous processes.
    """
    import asyncio
    try:
        result = asyncio.run(scrape_reel(url, prefer_proxy=prefer_proxy))
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.task(name="app.tasks.scheduled_fetch")
def scheduled_fetch(url):
    return enqueue_reel.delay(url)
