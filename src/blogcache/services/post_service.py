import asyncio
import json
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import CacheError
from ..core.exceptions import DatabaseError
from ..core.logging import log
from ..models.post import Post
from ..schemas.post import PostCreate
from ..schemas.post import PostResponse
from ..schemas.post import PostUpdate


class PostService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_prefix = "post:"
        self.cache_ttl = 300  # 5 minutes

    def _cache_key(self, post_id: int) -> str:
        return f"{self.cache_prefix}{post_id}"

    def _view_key(self, post_id: int, client_ip: str) -> str:
        """Generate Redis key for tracking unique views"""
        return f"view:{post_id}:{client_ip}"

    async def create_post(self, post_data: PostCreate) -> PostResponse:
        """Create a new post"""
        try:
            db_post = Post(**post_data.model_dump())
            self.db.add(db_post)
            await self.db.commit()
            await self.db.refresh(db_post)
            log.info("Created post id={} title={}", db_post.id, db_post.title)
            return PostResponse.model_validate(db_post)
        except SQLAlchemyError as e:
            await self.db.rollback()
            log.error("Database error creating post: {}", e)
            raise DatabaseError("create", e) from e

    async def get_post(
        self, post_id: int, client_ip: str = "unknown"
    ) -> Optional[PostResponse]:
        """Get post by ID with caching and unique view tracking"""
        cache_key = self._cache_key(post_id)

        try:
            cached = await self.redis.get(cache_key)
            if cached:
                log.debug("Cache hit for post_id={}", post_id)
                asyncio.create_task(
                    self._increment_views_in_background(post_id, client_ip)
                )
                return PostResponse(**json.loads(cached))
        except Exception as e:
            # Cache errors are non-critical, log and fallback to DB
            log.warning(
                "Cache get failed for post_id={}, falling back to DB: {}", post_id, e
            )

        log.debug("Cache miss for post_id={}, querying database", post_id)

        try:
            result = await self.db.execute(select(Post).where(Post.id == post_id))
            db_post = result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error("Database error fetching post_id={}: {}", post_id, e)
            raise DatabaseError("select", e) from e

        if not db_post:
            log.debug("Post not found: post_id={}", post_id)
            return None

        should_increment = await self._should_increment_view(post_id, client_ip)
        if should_increment:
            try:
                await self.db.execute(
                    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
                    {"id": post_id},
                )
                await self.db.commit()
                await self.db.refresh(db_post)
                log.debug(
                    "Incremented views for post_id={} from ip={}", post_id, client_ip
                )
            except SQLAlchemyError as e:
                await self.db.rollback()
                log.error(
                    "Database error incrementing views for post_id={}: {}", post_id, e
                )
                raise DatabaseError("update", e) from e

        post_response = PostResponse.model_validate(db_post)

        try:
            await self.redis.setex(
                cache_key,
                self.cache_ttl,
                post_response.model_dump_json(),
            )
            log.debug("Cached post_id={} with TTL={}s", post_id, self.cache_ttl)
        except Exception as e:
            # Cache errors are non-critical, log and continue
            log.warning("Cache set failed for post_id={}: {}", post_id, e)

        return post_response

    async def _should_increment_view(self, post_id: int, client_ip: str) -> bool:
        """Check if view should be counted (once per IP per 24h)"""
        view_key = self._view_key(post_id, client_ip)

        try:
            exists = await self.redis.exists(view_key)
            if not exists:
                await self.redis.setex(view_key, 86400, "1")  # 24 hours
                return True
            return False
        except Exception as e:
            # Cache errors are non-critical, fallback to counting the view
            log.warning(
                "Cache check failed for view tracking post_id={} ip={}: {}",
                post_id,
                client_ip,
                e,
            )
            return True

    async def _increment_views_in_background(
        self, post_id: int, client_ip: str
    ) -> None:
        """Increment views atomically if unique and invalidate cache"""
        try:
            should_increment = await self._should_increment_view(post_id, client_ip)
            if not should_increment:
                return

            from sqlalchemy.ext.asyncio import async_sessionmaker

            from ..core.database import engine

            AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
                    {"id": post_id},
                )
                await session.commit()

            await self.redis.delete(self._cache_key(post_id))
            log.debug(
                "Background view increment for post_id={} from ip={}",
                post_id,
                client_ip,
            )
        except (CacheError, DatabaseError):
            # Already logged, don't re-raise in background task
            pass
        except Exception as e:
            log.error(
                "Unexpected error incrementing views for post_id={}: {}", post_id, e
            )

    async def update_post(
        self, post_id: int, post_data: PostUpdate
    ) -> Optional[PostResponse]:
        """Update post and invalidate cache"""
        try:
            result = await self.db.execute(select(Post).where(Post.id == post_id))
            db_post = result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error("Database error fetching post_id={} for update: {}", post_id, e)
            raise DatabaseError("select", e) from e

        if not db_post:
            log.debug("Update failed: post_id={} not found", post_id)
            return None

        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(db_post)
        except SQLAlchemyError as e:
            await self.db.rollback()
            log.error("Database error updating post_id={}: {}", post_id, e)
            raise DatabaseError("update", e) from e

        cache_key = self._cache_key(post_id)
        try:
            await self.redis.delete(cache_key)
            log.info("Updated post_id={}, invalidated cache", post_id)
        except Exception as e:
            # Cache invalidation failure is non-critical
            log.warning("Cache delete failed for post_id={}: {}", post_id, e)

        return PostResponse.model_validate(db_post)

    async def delete_post(self, post_id: int) -> bool:
        """Delete post and invalidate cache"""
        try:
            result = await self.db.execute(
                delete(Post).where(Post.id == post_id).returning(Post.id)
            )
            deleted_id = result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error("Database error deleting post_id={}: {}", post_id, e)
            raise DatabaseError("delete", e) from e

        if deleted_id:
            cache_key = self._cache_key(post_id)
            try:
                await self.redis.delete(cache_key)
                await self.db.commit()
                log.info("Deleted post_id={}, invalidated cache", post_id)
            except Exception as e:
                await self.db.rollback()
                # Cache invalidation failure is non-critical
                log.warning("Cache delete failed for post_id={}: {}", post_id, e)
            return True

        log.debug("Delete failed: post_id={} not found", post_id)
        return False

    async def get_all_posts(
        self, skip: int = 0, limit: int = 100
    ) -> list[PostResponse]:
        """Get all posts with pagination"""
        try:
            result = await self.db.execute(
                select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit)
            )
            posts = result.scalars().all()
            return [PostResponse.model_validate(post) for post in posts]
        except SQLAlchemyError as e:
            log.error("Database error fetching posts: {}", e)
            raise DatabaseError("select", e) from e
