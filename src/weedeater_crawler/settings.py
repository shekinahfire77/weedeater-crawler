import os

BOT_NAME = "weedeater-crawler"
SPIDER_MODULES = ["weedeater_crawler.spiders"]
NEWSPIDER_MODULE = "weedeater_crawler.spiders"

ROBOTSTXT_OBEY = False  # Set True if you choose to obey

# Concurrency and throttling
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "8"))
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv("CONCURRENT_REQUESTS_PER_DOMAIN", "4"))
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", "0.5"))

AUTOTHROTTLE_ENABLED = os.getenv("AUTOTHROTTLE_ENABLED", "true").lower() == "true"
AUTOTHROTTLE_START_DELAY = float(os.getenv("AUTOTHROTTLE_START_DELAY", "0.5"))
AUTOTHROTTLE_MAX_DELAY = float(os.getenv("AUTOTHROTTLE_MAX_DELAY", "10.0"))
AUTOTHROTTLE_TARGET_CONCURRENCY = float(os.getenv("AUTOTHROTTLE_TARGET_CONCURRENCY", "2.0"))

# Memory guard
MEMUSAGE_LIMIT_MB = int(os.getenv("MEMUSAGE_LIMIT_MB", "2048"))

# Downloader Middlewares
DOWNLOADER_MIDDLEWARES = {
    "weedeater_crawler.middlewares.UserAgentRotationMiddleware": 400,
    "weedeater_crawler.middlewares.ProxyRotationMiddleware": 410,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "weedeater_crawler.middlewares.RateLimitRetryMiddleware": 550,
    "scrapy_playwright.middleware.ScrapyPlaywrightDownloadHandler": 800,
}

# Retry
RETRY_ENABLED = True
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524]
RETRY_TIMES = 5

# Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60_000
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": os.getenv("HEADLESS", "true").lower() == "true",
    "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
}
PLAYWRIGHT_DEFAULT_NAVIGATION_WAIT = "networkidle"
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "user_agent": None,  # set per-request via UA middleware
        "java_script_enabled": True,
        "ignore_https_errors": True,
        "viewport": {"width": 1366, "height": 900},
    }
}
PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None

# Block heavy resources for speed
PLAYWRIGHT_ABORT_REQUEST = re_compile = __import__('re').compile
PLAYWRIGHT_ABORT_REQUEST = [
    re_compile(r"\.(?:png|jpg|jpeg|gif|svg|ico)(\?.*)?$", re.I),
    re_compile(r"https?://www\.google-analytics\.com/.*", re.I),
    re_compile(r"https?://connect\.facebook\.net/.*", re.I),
]

# Scrapy-Redis for distributed crawling
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
SCHEDULER_PERSIST = True
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Pipelines
ITEM_PIPELINES = {
    "weedeater_crawler.pipelines.CloudStorageRawHTMLPipeline": 100,
    "weedeater_crawler.pipelines.SQLitePipeline": 200,
    "weedeater_crawler.pipelines.FirestorePipeline": 300,
}

# Extensions
EXTENSIONS = {
    "weedeater_crawler.extensions.PrometheusExtension": 100,
}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
