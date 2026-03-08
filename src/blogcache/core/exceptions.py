"""Custom exceptions for blogcache application.

This module defines domain-specific exceptions that provide better
error handling and type safety compared to generic exceptions.
"""


class BlogCacheException(Exception):
    """Base exception for all blogcache errors."""

    pass


class PostNotFoundError(BlogCacheException):
    """Raised when a post is not found in the database."""

    def __init__(self, post_id: int):
        self.post_id = post_id
        super().__init__(f"Post with id={post_id} not found")


class CacheError(BlogCacheException):
    """Raised when cache operations fail."""

    def __init__(self, operation: str, key: str, original_error: Exception):
        self.operation = operation
        self.key = key
        self.original_error = original_error
        super().__init__(f"Cache {operation} failed for key={key}: {original_error}")


class DatabaseError(BlogCacheException):
    """Raised when database operations fail."""

    def __init__(self, operation: str, original_error: Exception):
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"Database {operation} failed: {original_error}")
