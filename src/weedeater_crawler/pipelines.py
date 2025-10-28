import os
import json
import sqlite3
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timezone

from .utils.storage import get_firestore, upload_s3, upload_gcs, ensure_dir

class SQLitePipeline:
    # WARNING: SQLite has limited concurrent write support. For production concurrent crawls,
    # consider setting CONCURRENT_ITEMS = 1 in settings.py when using SQLite, or use PostgreSQL/MySQL instead.

    def open_spider(self, spider):
        if os.getenv("ENABLE_SQLITE", "true").lower() != "true":
            self.conn = None
            self.lock = None
            return
        path = os.getenv("SQLITE_PATH", "data/weedeater.sqlite")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # Allow connection to be used across threads with check_same_thread=False
        # Use threading.Lock() to serialize writes
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                source_url TEXT,
                crawled_at TEXT,
                site TEXT,
                brand TEXT,
                product_name TEXT,
                sku TEXT,
                upc TEXT,
                category TEXT,
                price TEXT,
                currency TEXT,
                availability TEXT,
                description TEXT,
                specs TEXT,
                images TEXT,
                breadcrumbs TEXT,
                raw_html_path TEXT
            )
            """
        )

    def close_spider(self, spider):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def process_item(self, item, spider):
        if not self.conn:
            return item
        # Use lock to ensure thread-safe writes
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO products (
                    source_url, crawled_at, site, brand, product_name, sku, upc, category,
                    price, currency, availability, description, specs, images, breadcrumbs, raw_html_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get('source_url'), item.get('crawled_at'), item.get('site'), item.get('brand'),
                    item.get('product_name'), item.get('sku'), item.get('upc'), item.get('category'),
                    item.get('price'), item.get('currency'), item.get('availability'), item.get('description'),
                    json.dumps(item.get('specs') or {}), json.dumps(item.get('images') or []),
                    json.dumps(item.get('breadcrumbs') or []), item.get('raw_html_path')
                )
            )
        return item

class FirestorePipeline:
    def open_spider(self, spider):
        self.client = get_firestore()
        self.collection = os.getenv("FIRESTORE_COLLECTION", "weedeater_products")

    def process_item(self, item, spider):
        if not self.client:
            return item
        key = item.get('sku') or item.get('source_url')
        # Use SHA256 to generate deterministic, valid Firestore document IDs
        # (hash() is not deterministic across Python sessions and can return negative values)
        doc_id = hashlib.sha256(str(key).encode('utf-8')).hexdigest()
        self.client.collection(self.collection).document(doc_id).set(dict(item))
        return item

class CloudStorageRawHTMLPipeline:
    # Optional: store raw HTML snapshots to S3 or GCS for auditability
    def process_item(self, item, spider):
        html_bytes = item.get('_raw_html_bytes')
        if not html_bytes:
            return item
        prefix = os.getenv('S3_PREFIX', 'weedeater/')
        gprefix = os.getenv('GCS_PREFIX', 'weedeater/')
        # Use SHA256 for deterministic hashing and datetime.now(timezone.utc) instead of deprecated utcnow()
        url_hash = hashlib.sha256(str(item.get('source_url')).encode('utf-8')).hexdigest()[:16]
        timestamp = int(datetime.now(timezone.utc).timestamp())
        if os.getenv('ENABLE_S3', 'false').lower() == 'true':
            key = f"{prefix}{timestamp}_{url_hash}.html"
            upload_s3(os.getenv('AWS_S3_BUCKET'), key, html_bytes)
            item['raw_html_path'] = f"s3://{os.getenv('AWS_S3_BUCKET')}/{key}"
        if os.getenv('ENABLE_GCS', 'false').lower() == 'true':
            key = f"{gprefix}{timestamp}_{url_hash}.html"
            upload_gcs(os.getenv('GCS_BUCKET'), key, html_bytes)
            item['raw_html_path'] = f"gs://{os.getenv('GCS_BUCKET')}/{key}"
        item.pop('_raw_html_bytes', None)
        return item
