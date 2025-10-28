import os
import json
import time
import tldextract
from datetime import datetime, timezone
from urllib.parse import urljoin
from typing import Iterable
from pathlib import Path

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy_playwright.page import PageMethod

from weedeater_crawler.items import ProductItem
from weedeater_crawler.utils.nav import infinite_scroll, login_sequence


class WeedeaterSpider(scrapy.Spider):
    name = "weedeater"
    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90_000,
    }

    def start_requests(self) -> Iterable[scrapy.Request]:
        # If running through Redis, seeds can be pushed via rpush to <spider>:start_urls
        # Fallback: read local YAML
        # Use environment variable for seeds path with fallback
        seeds_path_str = os.getenv(
            'WEEDEATER_SEEDS_PATH',
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "seeds", "weedeater_targets.yaml")
        )
        seeds_path = Path(seeds_path_str)

        try:
            import yaml
            with open(seeds_path, "r", encoding="utf-8") as f:
                seeds = yaml.safe_load(f)
                if not seeds:
                    seeds = []
        except FileNotFoundError:
            self.logger.error(f"Seeds file not found at {seeds_path}")
            seeds = []
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML from {seeds_path}: {e}")
            seeds = []
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to read seeds file at {seeds_path}: {e}")
            seeds = []
        for s in seeds:
            url = s["url"]
            meta = {
                "site": s.get("site"),
                "allow_patterns": s.get("allow_patterns"),
                "deny_patterns": s.get("deny_patterns"),
                "scroll_to_load": s.get("scroll_to_load", False),
                "type": s.get("type"),
                "playwright": True,
                "playwright_context": "default",
                "playwright_page_methods": [PageMethod("wait_for_load_state", state="networkidle")],
            }
            yield scrapy.Request(url, callback=self.parse_listing, meta=meta)

    def parse_listing(self, response: scrapy.http.Response):
        site = response.meta.get("site") or tldextract.extract(response.url).registered_domain
        allow = response.meta.get("allow_patterns") or []
        deny = response.meta.get("deny_patterns") or []

        # Optionally scroll to load more products
        if response.meta.get("scroll_to_load"):
            yield response.follow(
                response.url,
                callback=self.parse_listing_final,
                meta={
                    **response.meta,
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "body"),
                        *infinite_scroll(max_rounds=12, scroll_delay=0.6),
                        PageMethod("wait_for_load_state", state="networkidle"),
                    ],
                },
                dont_filter=True,
            )
            return

        # No scroll path: continue to link extraction now
        yield from self._extract_and_follow(response, allow, deny)

    def parse_listing_final(self, response: scrapy.http.Response):
        allow = response.meta.get("allow_patterns") or []
        deny = response.meta.get("deny_patterns") or []
        yield from self._extract_and_follow(response, allow, deny)

    def _extract_and_follow(self, response, allow, deny):
        # Extract product and pagination links
        le = LinkExtractor(allow=allow or (), deny=deny or ())
        for link in le.extract_links(response):
            href = link.url
            if any(p in href for p in ["/product/", "/products/", "/p/"]):
                yield response.follow(href, callback=self.parse_product, meta={**response.meta, "playwright": True})
            else:
                yield response.follow(href, callback=self.parse_listing, meta={**response.meta, "playwright": True})

    def parse_product(self, response: scrapy.http.Response):
        item = ProductItem()
        item['source_url'] = response.url
        item['crawled_at'] = datetime.now(timezone.utc).isoformat()
        item['site'] = response.meta.get('site')

        # Heuristics for product extraction across varied templates
        sel = response.css
        item['product_name'] = sel('h1::text').get() or sel('h1 span::text').get()
        item['brand'] = sel('[itemprop="brand"]::text').get() or sel('.brand::text').get() or sel('meta[itemprop="brand"]::attr(content)').get()
        item['sku'] = sel('[itemprop="sku"]::text').get() or sel('span.sku::text').get() or sel('meta[itemprop="sku"]::attr(content)').get()
        item['upc'] = sel('[itemprop="gtin13"]::attr(content)').get() or sel('[data-upc]::attr(data-upc)').get()
        item['price'] = sel('[itemprop="price"]::attr(content)').get() or sel('.price ::text').re_first(r"\$?([0-9,.]+)")
        item['currency'] = sel('[itemprop="priceCurrency"]::attr(content)').get() or 'USD'
        item['availability'] = sel('[itemprop="availability"]::attr(content)').re_first(r"InStock|OutOfStock|PreOrder")
        item['description'] = ' '.join(sel('[itemprop="description"] ::text').getall() or sel('.description ::text').getall()).strip()
        specs = {}
        for row in sel('table, .specs, .product-specs').css('tr'):
            key = ' '.join(row.css('th, .label ::text').getall()).strip()
            val = ' '.join(row.css('td, .value ::text').getall()).strip()
            if key and val:
                specs[key] = val
        item['specs'] = specs or None
        item['images'] = response.css('img::attr(src), img::attr(data-src), img::attr(data-original)').getall()
        item['breadcrumbs'] = [b.strip() for b in response.css('nav.breadcrumbs a::text, .breadcrumbs a::text').getall() if b.strip()]

        # Attach raw HTML for audit if enabled via pipeline
        item['_raw_html_bytes'] = response.text.encode('utf-8')

        yield item
