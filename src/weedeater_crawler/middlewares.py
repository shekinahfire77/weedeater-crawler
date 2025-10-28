import os
from typing import Optional
from scrapy import signals
from scrapy.http import Request
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from twisted.internet import defer
from twisted.internet.task import deferLater
from twisted.internet import reactor

from .utils.ua import get_user_agent
from .utils.proxy import get_proxy

class UserAgentRotationMiddleware:
    def process_request(self, request: Request, spider):
        ua = get_user_agent()
        request.headers['User-Agent'] = ua

class ProxyRotationMiddleware:
    def process_request(self, request: Request, spider):
        proxy = get_proxy()
        if proxy:
            request.meta['proxy'] = proxy

class RateLimitRetryMiddleware(RetryMiddleware):
    # Handle 429 with exponential backoff using Retry-After if present
    # Use Scrapy's built-in retry mechanism with DOWNLOAD_DELAY instead of blocking with time.sleep()
    def process_response(self, request, response, spider):
        if response.status == 429:
            retry_after = response.headers.get(b'Retry-After')
            if retry_after:
                try:
                    delay = int(retry_after.decode())
                except Exception:
                    delay = 2
            else:
                delay = 2
            # Store the delay in request meta for the retry middleware to respect
            request.meta['download_delay'] = delay
            spider.logger.warning(f"Rate limited (429) on {request.url}, will retry after {delay}s")
            # Let Scrapy's retry middleware handle the retry
            return self._retry(request, f"rate_limited_429", spider) or response
        return response
