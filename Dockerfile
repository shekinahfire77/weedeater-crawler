FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y git curl wget fonts-liberation libnss3 xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
RUN pip install -e . && python -m playwright install chromium --with-deps

COPY . /app

# Resource controls via env and scrapy settings
ENV HEADLESS=true CONCURRENT_REQUESTS=8 CONCURRENT_REQUESTS_PER_DOMAIN=4 DOWNLOAD_DELAY=0.5 MEMUSAGE_LIMIT_MB=2048

# Prometheus metrics on 8008
EXPOSE 8008

CMD ["scrapy", "crawl", "weedeater", "-s", "LOG_LEVEL=INFO"]
