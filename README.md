# Reels Scraper (Playwright + FastAPI + Celery + Postgres + MinIO)

## Setup
1. Copy `.env.example` → `.env` and edit values (DB, Redis, MinIO, optional proxies/CAPTCHA).
2. Initialize the database schema:
   - Start the stack once, or run psql manually:
     ```
     docker-compose up -d postgres
     docker-compose exec postgres bash
     psql -U reeluser -d reels -c "CREATE TABLE ..." -f /app/schema.sql
     ```
   - Alternatively run a local psql client and import `schema.sql`.

3. Start the stack:

## docker-compose up –build

- The API will be at http://localhost:8000
- MinIO web UI at http://localhost:9001 (user: minioadmin / minioadmin)

## Usage
- Enqueue a scrape:

## POST http://localhost:8000/scrape
## Body: { “url”: “https://www.facebook.com/…/reel/123” }

- Check Celery worker logs to see job status.

## Notes & production concerns
- Use high-quality **residential proxies**. Set `PROXY_LIST` in `.env`.
- `AUTO_SOLVE=false` by default. If you enable auto-solve, set `CAPTCHA_API_KEY` and understand legal/ToS risk.
- Replace MinIO with AWS S3 in production (update storage.py).
- For multi-worker proxy counters, use Redis atomic counters (instead of in-memory).
- Consider Kubernetes / autoscaling if you need large scale.
