"""Main application entrypoint.

This module creates and configures the FastAPI application,
including routers and lifecycle events.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from typing import Dict

from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from .api import posts
from .core.config import settings
from .core.database import engine
from .core.database import redis_client
from .core.exceptions import BlogCacheException
from .core.exceptions import PostNotFoundError
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

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        log.success("✓ PostgreSQL connection established")
    except Exception as e:
        log.error("✗ PostgreSQL connection failed: {}", e)
        raise

    try:
        await redis_client.ping()  # type: ignore[misc]
        log.success("✓ Redis connection established")
    except Exception as e:
        log.error("✗ Redis connection failed: {}", e)
        raise

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
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="High-performance blog API with Redis caching",
        description="Blog API with Redis Cache-Aside pattern and atomic view counter",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.include_router(posts.router)

    @application.exception_handler(PostNotFoundError)
    async def post_not_found_handler(
        request: Request, exc: PostNotFoundError
    ) -> JSONResponse:
        """Handle PostNotFoundError exceptions."""
        log.debug("Post not found: post_id={}", exc.post_id)
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @application.exception_handler(BlogCacheException)
    async def blogcache_exception_handler(
        request: Request, exc: BlogCacheException
    ) -> JSONResponse:
        """Handle generic BlogCacheException exceptions."""
        log.error("BlogCache error: {}", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @application.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root path to API documentation."""
        return RedirectResponse(url="/docs")

    @application.get("/health")
    async def health_check() -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.app_name}

    return application


app = create_app()
