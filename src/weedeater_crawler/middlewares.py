import os
import time
from typing import Optional
from scrapy import signals
from scrapy.http import Request
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from tenacity import retry, stop_after_attempt, wait_exponential

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
    def _retry(self, request, reason, spider):
        response = getattr(reason, 'response', None)
        if response and response.status == 429:
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                try:
                    delay = int(retry_after.decode())
                except Exception:
                    delay = 2
            else:
                delay = 2
            time.sleep(delay)
        return super()._retry(request, reason, spider)
