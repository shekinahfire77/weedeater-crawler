#!/bin/bash
set -e

echo "==================================="
echo "Weedeater Crawler Starting..."
echo "==================================="

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
until nc -z ${REDIS_URL##redis://} 2>/dev/null; do
    # Extract host and port from REDIS_URL
    REDIS_HOST=$(echo $REDIS_URL | sed 's|redis://||' | cut -d':' -f1)
    REDIS_PORT=$(echo $REDIS_URL | sed 's|redis://||' | cut -d':' -f2)

    echo "Attempting to connect to Redis at $REDIS_HOST:$REDIS_PORT..."

    # Simple wait without nc dependency
    sleep 2

    # Try to use redis-cli if available, otherwise continue
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h $REDIS_HOST -p $REDIS_PORT ping 2>/dev/null | grep -q PONG; then
            break
        fi
    else
        # If redis-cli not available, just wait a bit and hope for the best
        sleep 3
        break
    fi
done

echo "Redis is ready!"

# Ensure data and logs directories exist
mkdir -p /app/data /app/logs

# Print environment info
echo "-----------------------------------"
echo "Environment Configuration:"
echo "REDIS_URL: $REDIS_URL"
echo "HEADLESS: $HEADLESS"
echo "CONCURRENT_REQUESTS: $CONCURRENT_REQUESTS"
echo "SQLITE_PATH: $SQLITE_PATH"
echo "PROMETHEUS_PORT: $PROMETHEUS_PORT"
echo "-----------------------------------"

# Execute the main command
echo "Starting crawler with command: $@"
exec "$@"
