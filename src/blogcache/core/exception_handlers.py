"""Exception handlers for FastAPI application.

This module contains all exception handlers for custom exceptions,
keeping the main application file clean and focused.
"""

from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from .exceptions import BlogCacheException
from .exceptions import CacheError
from .exceptions import DatabaseError
from .exceptions import PostNotFoundError
from .logging import log


async def post_not_found_handler(
    request: Request, exc: PostNotFoundError
) -> JSONResponse:
    """Handle PostNotFoundError exceptions."""
    log.debug("Post not found: post_id={}", exc.post_id)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def cache_error_handler(request: Request, exc: CacheError) -> JSONResponse:
    """Handle CacheError exceptions (non-critical, log and continue)."""
    log.warning("Cache error: operation={} key={}", exc.operation, exc.key)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Cache operation failed"},
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle DatabaseError exceptions (critical)."""
    log.error("Database error: operation={}", exc.operation)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database operation failed"},
    )


async def blogcache_exception_handler(
    request: Request, exc: BlogCacheException
) -> JSONResponse:
    """Handle generic BlogCacheException exceptions."""
    log.error("BlogCache error: {}", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(PostNotFoundError, post_not_found_handler)
    app.add_exception_handler(CacheError, cache_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(BlogCacheException, blogcache_exception_handler)
