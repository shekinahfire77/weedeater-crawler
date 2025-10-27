# weedeater-crawler

A production-ready Scrapy + Playwright project for crawling weedeater manufacturer and distributor sites.

## Quickstart
```bash
# 1) Install deps
pip install -e .
python -m playwright install chromium

# 2) Configure env
cp .env.example .env
# edit .env with keys and toggles

# 3) Run with Redis-based distributed scheduler
#    Start Redis first
redis-server &

# 4) Seed targets
python tools/seed_queue.py seeds/weedeater_targets.yaml

# 5) Crawl (headless by default)
scrapy crawl weedeater -s LOG_LEVEL=INFO

# Headful for debugging
HEADLESS=false scrapy crawl weedeater -s LOG_LEVEL=DEBUG
```

## Key Features
- Dynamic rendering with Playwright. Auto-wait for network idle. Scroll-to-load.
- Smart navigation helpers: login, search form submit, pagination, product list/detail traversal.
- Retry with exponential backoff and 429 rate-limit handling.
- Proxy rotation and user-agent spoofing.
- Distributed, incremental crawling via `scrapy-redis` with persistent queues and dupefilter.
- Data sinks: Firestore, SQLite, S3/GCS. Toggle via settings.
- Throttling and resource caps with AutoThrottle and MEMUSAGE limits.
- Prometheus metrics exporter.

## Project layout
```
src/
  weedeater_crawler/
    __init__.py
    items.py
    settings.py
    middlewares.py
    pipelines.py
    extensions.py
    utils/
      __init__.py
      nav.py
      proxy.py
      ua.py
      storage.py
    spiders/
      weedeater_spider.py
seeds/
  weedeater_targets.yaml
tools/
  seed_queue.py
Dockerfile
.env.example
```

## Data Model
Common fields emitted by the spider:
- source_url, crawled_at, brand, product_name, sku, upc, category, price, currency,
  availability, description, specs (dict), images (list), breadcrumbs (list),
  raw_html_path (optional cloud path), site (domain)

## Distributed Mode
- Uses `scrapy_redis.scheduler.Scheduler` and `scrapy_redis.dupefilter.RFPDupeFilter`.
- Seed with `tools/seed_queue.py` or push redis keys manually.

## Compliance
- Respect robots.txt only if configured. You own compliance decisions. Configure `ROBOTSTXT_OBEY` and site-specific rules.
- Add allow/deny patterns in seeds to restrict scope.
