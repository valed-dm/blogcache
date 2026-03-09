"""Cache service for Redis operations.

This module provides a clean abstraction over Redis operations.
Redis failures are raised as CacheError for callers to handle or propagate.
"""

from typing import Optional

from redis.asyncio import Redis

from ..core.exceptions import CacheError
from ..core.metrics import cache_hits
from ..core.metrics import cache_misses


class CacheService:
    """Service for cache operations with error handling."""

    def __init__(self, redis: Redis, ttl: int = 300):
        """Initialize cache service.

        Args:
            redis: Redis client instance.
            ttl: Default time-to-live in seconds (default: 5 minutes).
        """
        self.redis = redis
        self.ttl = ttl

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.

        Raises:
            CacheError: If the Redis operation fails.
        """
        try:
            value = await self.redis.get(key)
            if value:
                cache_hits.labels(operation="cache_get").inc()
            else:
                cache_misses.labels(operation="cache_get").inc()
            return str(value) if value else None
        except Exception as e:
            raise CacheError("get", key, e) from e

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (uses default if not provided).

        Raises:
            CacheError: If the Redis operation fails.
        """
        try:
            await self.redis.setex(key, ttl or self.ttl, value)
        except Exception as e:
            raise CacheError("set", key, e) from e

    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key.

        Raises:
            CacheError: If the Redis operation fails.
        """
        try:
            await self.redis.delete(key)
        except Exception as e:
            raise CacheError("delete", key, e) from e

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if exists, False otherwise.

        Raises:
            CacheError: If the Redis operation fails.
        """
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            raise CacheError("exists", key, e) from e

    async def set_with_expiry(self, key: str, value: str, seconds: int) -> None:
        """Set value with custom expiry time.

        Args:
            key: Cache key.
            value: Value to cache.
            seconds: Expiry time in seconds.

        Raises:
            CacheError: If the Redis operation fails.
        """
        try:
            await self.redis.setex(key, seconds, value)
        except Exception as e:
            raise CacheError("set_with_expiry", key, e) from e
