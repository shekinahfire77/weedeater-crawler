import os
import sys
import yaml
import redis

if __name__ == "__main__":
    try:
        # Load seeds from YAML file
        seeds_file = os.getenv("WEEDEATER_SEEDS_PATH", "seeds/weedeater_targets.yaml")
        try:
            with open(seeds_file, "r", encoding="utf-8") as f:
                seeds = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"ERROR: Seeds file not found at '{seeds_file}'", file=sys.stderr)
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"ERROR: Failed to parse YAML from '{seeds_file}': {e}", file=sys.stderr)
            sys.exit(1)

        if not seeds:
            print("WARNING: No seeds found in YAML file", file=sys.stderr)
            sys.exit(0)

        # Connect to Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            r = redis.from_url(redis_url)
            # Test connection
            r.ping()
        except redis.ConnectionError as e:
            print(f"ERROR: Failed to connect to Redis at '{redis_url}': {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Redis connection error: {e}", file=sys.stderr)
            sys.exit(1)

        # Push seeds to Redis
        key = "weedeater:start_urls"
        for s in seeds:
            r.rpush(key, s["url"])  # minimal seeding; meta comes from YAML in spider

        print(f"Successfully seeded {len(seeds)} urls into Redis key '{key}'")
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
