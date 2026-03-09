"""Prometheus metrics for monitoring application performance.

This module provides metrics for cache hits/misses, request duration,
and other key performance indicators.
"""

from prometheus_client import Counter
from prometheus_client import Histogram


# Cache metrics (business-level: e.g. get_post served from cache vs DB)
cache_hits = Counter(
    "blogcache_cache_hits_total",
    "Total number of cache hits by operation (e.g. get_post)",
    ["operation"],
)

cache_misses = Counter(
    "blogcache_cache_misses_total",
    "Total number of cache misses by operation (e.g. get_post)",
    ["operation"],
)

# Cache backend metrics (low-level: every Redis get hit/miss)
cache_backend_hits = Counter(
    "blogcache_cache_backend_hits_total",
    "Total number of Redis cache get() hits (low-level cache layer)",
)

cache_backend_misses = Counter(
    "blogcache_cache_backend_misses_total",
    "Total number of Redis cache get() misses (low-level cache layer)",
)

# Request metrics
request_duration = Histogram(
    "blogcache_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)

# Post metrics
posts_created = Counter(
    "blogcache_posts_created_total",
    "Total number of posts created",
)

posts_viewed = Counter(
    "blogcache_posts_viewed_total",
    "Total number of post views",
)

# Database metrics
db_queries = Counter(
    "blogcache_db_queries_total",
    "Total number of database queries",
    ["operation"],
)

db_errors = Counter(
    "blogcache_db_errors_total",
    "Total number of database errors",
    ["operation"],
)
