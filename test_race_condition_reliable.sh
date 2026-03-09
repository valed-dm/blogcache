#!/bin/bash

# Race Condition Test - Reliable Version
# Tests atomic view counter with cache clearing between requests

POST_ID=$1
REQUESTS=50

if [ -z "$POST_ID" ]; then
  echo "Usage: $0 <POST_ID>"
  exit 1
fi

echo "Testing $REQUESTS concurrent requests with atomic view counter..."
echo "Post ID: $POST_ID"

# Clear cache and view tracking before test
echo "Clearing cache and view tracking..."
docker exec blogcache_redis redis-cli DEL "post:$POST_ID" > /dev/null 2>&1
docker exec blogcache_redis redis-cli KEYS "view:$POST_ID:*" | xargs -I {} docker exec blogcache_redis redis-cli DEL {} > /dev/null 2>&1

# Get initial view count
INITIAL_VIEWS=$(curl -s http://localhost:8000/posts/$POST_ID | grep -o '"views":[0-9]*' | cut -d':' -f2)
echo "Initial views: $INITIAL_VIEWS"

# Clear cache again to force all requests to hit DB
docker exec blogcache_redis redis-cli DEL "post:$POST_ID" > /dev/null 2>&1

echo "Launching $REQUESTS concurrent requests..."

# Launch concurrent requests with different IPs
for i in $(seq 1 $REQUESTS); do
  curl -s -H "X-Forwarded-For: 10.0.0.$i" \
    http://localhost:8000/posts/$POST_ID > /dev/null &
done

# Wait for all requests to complete
wait

echo "All requests completed. Waiting for any background tasks..."
sleep 3

# Clear cache to force fresh read from DB
docker exec blogcache_redis redis-cli DEL "post:$POST_ID" > /dev/null 2>&1

# Get final view count
FINAL_VIEWS=$(curl -s http://localhost:8000/posts/$POST_ID | grep -o '"views":[0-9]*' | cut -d':' -f2)
EXPECTED=$((INITIAL_VIEWS + REQUESTS))

echo ""
echo "Results:"
echo "--------"
echo "Initial views:  $INITIAL_VIEWS"
echo "Requests sent:  $REQUESTS"
echo "Expected views: $EXPECTED"
echo "Actual views:   $FINAL_VIEWS"
echo ""

if [ "$FINAL_VIEWS" -eq "$EXPECTED" ]; then
  echo "✅ PASS: No race condition detected!"
  echo "All $REQUESTS concurrent increments were applied atomically."
  exit 0
else
  LOST=$((EXPECTED - FINAL_VIEWS))
  echo "❌ FAIL: Race condition detected!"
  echo "Lost updates: $LOST (expected $EXPECTED, got $FINAL_VIEWS)"
  exit 1
fi
