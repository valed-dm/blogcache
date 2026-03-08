"""Health check service for monitoring application dependencies.

This module provides health checks for database and cache connectivity.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from .logging import log


class HealthCheckService:
    """Service for checking health of application dependencies."""

    @staticmethod
    async def check_postgres(engine: AsyncEngine) -> bool:
        """Check PostgreSQL connectivity.

        Args:
            engine: SQLAlchemy async engine.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            log.error("PostgreSQL health check failed: {}", e)
            return False

    @staticmethod
    async def check_redis(redis_client) -> bool:
        """Check Redis connectivity.

        Args:
            redis_client: Redis client instance.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            await redis_client.ping()
            return True
        except Exception as e:
            log.error("Redis health check failed: {}", e)
            return False
