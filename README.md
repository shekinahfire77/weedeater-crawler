# weedeater-crawler

A production-ready Scrapy + Playwright project for crawling weedeater manufacturer and distributor sites.

## Quick Start with Docker (Recommended)

The easiest way to run the crawler is using Docker Compose:

```bash
# 1) Clone the repository
git clone <repository-url>
cd weedeater-crawler

# 2) Build and start services (Redis + Crawler)
docker-compose up -d

# 3) Seed the Redis queue with targets
docker-compose --profile seed up seed-queue

# 4) View logs
docker-compose logs -f crawler

# 5) Stop services
docker-compose down

# 6) Stop and remove all data (including Redis and SQLite)
docker-compose down -v
```

### Docker Commands Reference

```bash
# Build the Docker image
docker-compose build

# Start services in background
docker-compose up -d

# View crawler logs in real-time
docker-compose logs -f crawler

# View Redis logs
docker-compose logs -f redis

# Execute a command in the running crawler container
docker-compose exec crawler bash

# Run a custom Scrapy command
docker-compose exec crawler scrapy crawl weedeater -s LOG_LEVEL=DEBUG

# Restart the crawler
docker-compose restart crawler

# Access the data
# SQLite database: ./data/weedeater.sqlite
# Logs: ./logs/

# View Prometheus metrics
curl http://localhost:8008/metrics
```

### Environment Configuration

Edit the `docker-compose.yml` file to customize environment variables, or create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env
# Edit .env with your configuration
```

Key environment variables:
- `REDIS_URL`: Redis connection string (default: redis://redis:6379)
- `HEADLESS`: Run browser in headless mode (default: true)
- `CONCURRENT_REQUESTS`: Max concurrent requests (default: 8)
- `SQLITE_PATH`: Path to SQLite database (default: /app/data/weedeater.sqlite)
- `ENABLE_FIRESTORE`, `ENABLE_S3`, `ENABLE_GCS`: Toggle cloud storage backends
- `PROMETHEUS_PORT`: Metrics export port (default: 8008)

## Local Development (Without Docker)

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

## Docker Architecture

The containerized setup includes:

1. **Redis Service**: Persistent queue storage for distributed crawling
   - Uses Redis 7 Alpine for minimal footprint
   - Data persisted in named volume `redis-data`
   - Health checks ensure service is ready before crawler starts

2. **Crawler Service**: Main Scrapy application
   - Built from local Dockerfile
   - Mounts `./data` and `./logs` directories for persistence
   - Exposes port 8008 for Prometheus metrics
   - Includes Playwright + Chromium with all dependencies
   - Resource limits: 2.5GB max memory, 1GB reserved

3. **Seed Queue Service** (optional, profile: seed)
   - Runs once to populate Redis with initial URLs
   - Uses same image as crawler
   - Automatically exits after seeding

### Data Persistence

- **SQLite Database**: `./data/weedeater.sqlite` (mounted volume)
- **Logs**: `./logs/` (mounted volume)
- **Redis Data**: Named volume `redis-data` (persists between restarts)

### Networking

All services communicate via the `weedeater-network` bridge network. Services can reference each other by service name (e.g., `redis://redis:6379`).
