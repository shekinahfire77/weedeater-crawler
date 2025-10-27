import os
import time
import json
from pathlib import Path
from typing import Optional

import boto3
from google.cloud import storage as gcs_storage
import firebase_admin
from firebase_admin import credentials, firestore

_firestore_client = None


def ensure_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_firestore():
    global _firestore_client
    if _firestore_client:
        return _firestore_client
    if os.getenv("ENABLE_FIRESTORE", "false").lower() != "true":
        return None
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not firebase_admin._apps:
        if cred_json and Path(cred_json).exists():
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred, {
                'projectId': os.getenv("FIREBASE_PROJECT_ID")
            })
        else:
            firebase_admin.initialize_app()
    _firestore_client = firestore.client()
    return _firestore_client


def upload_s3(bucket: str, key: str, data: bytes, content_type: str = "text/html"):
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)


def upload_gcs(bucket: str, key: str, data: bytes, content_type: str = "text/html"):
    client = gcs_storage.Client()
    b = client.bucket(bucket)
    blob = b.blob(key)
    blob.upload_from_string(data, content_type=content_type)
