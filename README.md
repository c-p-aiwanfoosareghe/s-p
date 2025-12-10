# Facebook Reels Scraper (Playwright + Celery + CAPTCHA handling)

## Quickstart (local/testing)
1. Copy `.env.example` → `.env` and fill values.
2. Build and run:

## docker-compose up –build

3. To queue a job (example using redis-cli or python):
- Use Python inside the worker container:
  ```
  docker-compose exec worker bash
  python -c "from app.tasks import enqueue_reel; enqueue_reel.delay('https://www.facebook.com/.../reel/123')"
  ```

## Production notes
- Use high-quality residential proxies to reduce captcha triggers.
- For multi-worker proxy usage counters, store usage counters in Redis instead of in-memory.
- CAPTCHA auto-solve is dangerous: set `AUTO_SOLVE=false` in production unless you fully understand legal/ToS implications.
- Replace MinIO defaults with AWS S3 credentials for production.
- Harden Playwright sandboxing and scale by running multiple worker replicas with a proxy pool and shared Redis counters.

## Legal / Ethics
- Only scrape public content.
- Respect robots, rate limits, and platform ToS.
- For large-scale commercial use, consult legal counsel.
