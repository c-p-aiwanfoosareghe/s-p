FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgbm1 \
    libpango-1.0-0 \
    libcups2 \
    libxdamage1 \
    libxfixes3 \
    libxext6 \
    libxkbcommon0 \
    libgtk-3-0 \
    curl \
    netcat-openbsd \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "main.py"]
