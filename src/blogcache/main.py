"""Main application entrypoint.

This module creates and configures the FastAPI application,
including routers and lifecycle events.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import generate_latest
from slowapi import Limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .api import posts
from .core.config import settings
from .core.database import engine
from .core.database import redis_client
from .core.exception_handlers import register_exception_handlers
from .core.health import HealthCheckService
from .core.logging import log


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events.

    Args:
        app: The FastAPI application instance.

    Yields:
        None
    """
    log.info("Starting {} application", settings.app_name)
    log.info("Debug mode: {}", settings.debug)
    log.info("Database: {}", settings.postgres_db)

    postgres_healthy = await HealthCheckService.check_postgres(engine)
    if not postgres_healthy:
        raise RuntimeError("PostgreSQL connection failed")
    log.success("✓ PostgreSQL connection established")

    redis_healthy = await HealthCheckService.check_redis(redis_client)
    if not redis_healthy:
        raise RuntimeError("Redis connection failed")
    log.success("✓ Redis connection established")

    log.info("Application startup complete")

    yield

    log.info("Shutting down {} application", settings.app_name)

    await engine.dispose()
    log.info("✓ Database connections closed")

    await redis_client.aclose()
    log.info("✓ Redis connection closed")

    log.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        The configured FastAPI application instance.
    """
    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="High-performance blog API with Redis caching",
        description="Blog API with Redis Cache-Aside pattern and atomic view counter",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add rate limiter to app state
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    application.include_router(posts.router)
    register_exception_handlers(application)

    @application.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root path to API documentation."""
        return RedirectResponse(url="/docs")

    @application.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint with detailed status."""
        postgres_healthy = await HealthCheckService.check_postgres(engine)
        redis_healthy = await HealthCheckService.check_redis(redis_client)

        checks = {
            "postgres": "healthy" if postgres_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
        }

        all_healthy = postgres_healthy and redis_healthy
        status_code = (
            status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if all_healthy else "unhealthy",
                "service": settings.app_name,
                "version": "0.1.0",
                "checks": checks,
            },
        )

    @application.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return application


app = create_app()
