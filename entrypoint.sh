#!/bin/bash
set -e

echo "==================================="
echo "Weedeater Crawler Starting..."
echo "==================================="

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."

# Extract host and port from REDIS_URL (format: redis://host:port or redis://host:port/db)
REDIS_URL_STRIPPED=$(echo "$REDIS_URL" | sed 's|redis://||' | sed 's|/.*||')
REDIS_HOST=$(echo "$REDIS_URL_STRIPPED" | cut -d':' -f1)
REDIS_PORT=$(echo "$REDIS_URL_STRIPPED" | cut -d':' -f2)

# Default to 6379 if port not specified
if [ -z "$REDIS_PORT" ] || [ "$REDIS_PORT" = "$REDIS_HOST" ]; then
    REDIS_PORT=6379
fi

echo "Attempting to connect to Redis at $REDIS_HOST:$REDIS_PORT..."

# Use bash TCP connection test (works without external dependencies)
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Try to open TCP connection to Redis using bash
    if timeout 2 bash -c "echo > /dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
        echo "Redis is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Redis not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES), waiting..."
    sleep 2
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "WARNING: Could not connect to Redis after $MAX_RETRIES attempts. Proceeding anyway..."
fi

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
