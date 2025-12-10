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
