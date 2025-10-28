from scrapy import Item, Field

class ProductItem(Item):
    source_url = Field()
    crawled_at = Field()
    site = Field()
    brand = Field()
    product_name = Field()
    sku = Field()
    upc = Field()
    category = Field()
    price = Field()
    currency = Field()
    availability = Field()
    description = Field()
    specs = Field()
    images = Field()
    breadcrumbs = Field()
    raw_html_path = Field()
    _raw_html_bytes = Field()  # Internal field for storing raw HTML before upload
