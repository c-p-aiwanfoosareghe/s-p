FROM python:3.11-slim

# system deps for Playwright and libs
RUN apt-get update && apt-get install -y wget gnupg ca-certificates libnss3 libatk1.0-0 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 libxrandr2 libasound2 libpangocairo-1.0-0 libgbm1 build-essential --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install Playwright browsers
RUN python -m playwright install --with-deps chromium

COPY . /app
ENV PYTHONUNBUFFERED=1
CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info", "--concurrency=1"]
