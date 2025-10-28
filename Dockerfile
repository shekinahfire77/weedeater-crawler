FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for Playwright and Scrapy
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    netcat-openbsd \
    fonts-liberation \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files first
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Install Playwright and Chromium
RUN python -m playwright install chromium --with-deps

# Setup entrypoint script
RUN chmod +x /app/entrypoint.sh

# Create directories for data persistence
RUN mkdir -p /app/data /app/logs

# Resource controls via env and scrapy settings
ENV HEADLESS=true \
    CONCURRENT_REQUESTS=8 \
    CONCURRENT_REQUESTS_PER_DOMAIN=4 \
    DOWNLOAD_DELAY=0.5 \
    MEMUSAGE_LIMIT_MB=2048 \
    REDIS_URL=redis://redis:6379 \
    ENABLE_SQLITE=true \
    SQLITE_PATH=/app/data/weedeater.sqlite \
    PROMETHEUS_PORT=8008

# Prometheus metrics port
EXPOSE 8008

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["scrapy", "crawl", "weedeater", "-s", "LOG_LEVEL=INFO"]
