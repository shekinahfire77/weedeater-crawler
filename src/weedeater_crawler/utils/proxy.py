import os
import random

_PROXY_POOL = None

def get_proxy():
    global _PROXY_POOL
    pool = os.getenv("PROXY_POOL", "").strip()
    if not pool:
        return None
    if _PROXY_POOL is None:
        _PROXY_POOL = [p.strip() for p in pool.split(",") if p.strip()]
    if not _PROXY_POOL:
        return None
    return random.choice(_PROXY_POOL)
