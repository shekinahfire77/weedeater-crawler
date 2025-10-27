import os
import yaml
import redis

if __name__ == "__main__":
    seeds = yaml.safe_load(open("seeds/weedeater_targets.yaml", "r", encoding="utf-8"))
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    key = "weedeater:start_urls"
    for s in seeds:
        r.rpush(key, s["url"])  # minimal seeding; meta comes from YAML in spider
    print(f"Seeded {len(seeds)} urls into {key}")
