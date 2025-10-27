import os
from prometheus_client import Counter, Gauge, start_http_server

class PrometheusExtension:
    def __init__(self, port: int = 8008):
        self.port = port
        self.started = False
        self.pages_crawled = Counter('pages_crawled', 'Total pages crawled')
        self.items_scraped = Counter('items_scraped', 'Total items scraped')
        self.failures = Counter('crawl_failures', 'Total request failures')
        self.in_queue = Gauge('redis_inqueue', 'Approx keys in queue')

    @classmethod
    def from_crawler(cls, crawler):
        port = int(os.getenv('PROMETHEUS_PORT', '8008'))
        ext = cls(port)
        crawler.signals.connect(ext.item_scraped, signal=crawler.signals.item_scraped)
        crawler.signals.connect(ext.request_dropped, signal=crawler.signals.request_dropped)
        crawler.signals.connect(ext.request_scheduled, signal=crawler.signals.request_scheduled)
        crawler.signals.connect(ext.spider_opened, signal=crawler.signals.spider_opened)
        return ext

    def spider_opened(self, spider):
        if not self.started:
            start_http_server(self.port)
            self.started = True

    def item_scraped(self, item, response, spider):
        self.items_scraped.inc()

    def request_scheduled(self, request, spider):
        self.pages_crawled.inc()

    def request_dropped(self, request, spider):
        self.failures.inc()
