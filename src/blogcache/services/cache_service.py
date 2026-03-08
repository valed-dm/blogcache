"""Cache service for Redis operations.

This module provides a clean abstraction over Redis operations
with error handling and logging.
"""

from typing import Optional

from redis.asyncio import Redis

from ..core.logging import log


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
            Cached value or None if not found or error occurred.
        """
        try:
            return await self.redis.get(key)
        except Exception as e:
            log.warning("Cache get failed for key={}: {}", key, e)
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (uses default if not provided).

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.redis.setex(key, ttl or self.ttl, value)
            return True
        except Exception as e:
            log.warning("Cache set failed for key={}: {}", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            log.warning("Cache delete failed for key={}: {}", key, e)
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key.

        Returns:
            True if exists, False otherwise (including on error).
        """
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            log.warning("Cache exists check failed for key={}: {}", key, e)
            return False

    async def set_with_expiry(self, key: str, value: str, seconds: int) -> bool:
        """Set value with custom expiry time.

        Args:
            key: Cache key.
            value: Value to cache.
            seconds: Expiry time in seconds.

        Returns:
            True if successful, False otherwise.
        """
        try:
            await self.redis.setex(key, seconds, value)
            return True
        except Exception as e:
            log.warning("Cache setex failed for key={}: {}", key, e)
            return False
