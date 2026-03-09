"""Repository for Post database operations.

This module provides the data access layer for Post entities,
separating database operations from business logic.
"""

from typing import Optional

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import DatabaseError
from ..core.logging import log
from ..core.metrics import db_errors
from ..core.metrics import db_queries
from ..models.post import Post


class PostRepository:
    """Repository for Post database operations."""

    def __init__(self, db: AsyncSession):
        """Initialize repository.

        Args:
            db: Database session.
        """
        self.db = db

    async def create(self, post: Post) -> Post:
        """Create a new post.

        Args:
            post: Post instance to create.

        Returns:
            Created post with ID.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            self.db.add(post)
            await self.db.commit()
            await self.db.refresh(post)
            db_queries.labels(operation="create").inc()
            return post
        except SQLAlchemyError as e:
            await self.db.rollback()
            db_errors.labels(operation="create").inc()
            log.error("Database error creating post: {}", e)
            raise DatabaseError("create", e) from e

    async def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by ID.

        Args:
            post_id: Post ID.

        Returns:
            Post instance or None if not found.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            result = await self.db.execute(select(Post).where(Post.id == post_id))
            row = result.scalar_one_or_none()
            db_queries.labels(operation="get_by_id").inc()
            return row
        except SQLAlchemyError as e:
            await self.db.rollback()
            db_errors.labels(operation="get_by_id").inc()
            log.error("Database error fetching post_id={}: {}", post_id, e)
            raise DatabaseError("select", e) from e

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Post]:
        """Get all posts with pagination.

        Args:
            skip: Number of posts to skip.
            limit: Maximum number of posts to return.

        Returns:
            List of posts.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            result = await self.db.execute(
                select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit)
            )
            rows = list(result.scalars().all())
            db_queries.labels(operation="get_all").inc()
            return rows
        except SQLAlchemyError as e:
            await self.db.rollback()
            db_errors.labels(operation="get_all").inc()
            log.error("Database error fetching posts: {}", e)
            raise DatabaseError("select", e) from e

    async def update(self, post: Post) -> Post:
        """Update post.

        Args:
            post: Post instance with updated fields.

        Returns:
            Updated post.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            await self.db.commit()
            await self.db.refresh(post)
            db_queries.labels(operation="update").inc()
            return post
        except SQLAlchemyError as e:
            await self.db.rollback()
            db_errors.labels(operation="update").inc()
            log.error("Database error updating post_id={}: {}", post.id, e)
            raise DatabaseError("update", e) from e

    async def delete(self, post_id: int) -> bool:
        """Delete post by ID.

        Args:
            post_id: Post ID.

        Returns:
            True if deleted, False if not found.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            result = await self.db.execute(
                delete(Post).where(Post.id == post_id).returning(Post.id)
            )
            deleted_id = result.scalar_one_or_none()
            if deleted_id:
                await self.db.commit()
                db_queries.labels(operation="delete").inc()
                return True
            return False
        except SQLAlchemyError as e:
            await self.db.rollback()
            db_errors.labels(operation="delete").inc()
            log.error("Database error deleting post_id={}: {}", post_id, e)
            raise DatabaseError("delete", e) from e

    async def increment_views(self, post_id: int) -> None:
        """Increment post views atomically.

        Args:
            post_id: Post ID.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            await self.db.execute(
                text("UPDATE posts SET views = views + 1 WHERE id = :id"),
                {"id": post_id},
            )
            await self.db.commit()
            db_queries.labels(operation="increment_views").inc()
            # Expire all cached instances to force fresh fetch
            self.db.expire_all()
        except SQLAlchemyError as e:
            await self.db.rollback()
            db_errors.labels(operation="increment_views").inc()
            log.error(
                "Database error incrementing views for post_id={}: {}", post_id, e
            )
            raise DatabaseError("update", e) from e
