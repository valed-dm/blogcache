import asyncio
import json
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import CacheError
from ..core.logging import log
from ..core.metrics import cache_hits
from ..core.metrics import cache_misses
from ..core.metrics import posts_created
from ..core.metrics import posts_viewed
from ..dto.post_dto import PostDTO
from ..models.post import Post
from ..repositories.post_repository import PostRepository
from ..schemas.post import PostCreate
from ..schemas.post import PostResponse
from ..schemas.post import PostUpdate
from .cache_service import CacheService


class PostService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.repository = PostRepository(db)
        self.cache = CacheService(redis, ttl=300)  # 5 minutes
        self.cache_prefix = "post:"
        self.view_prefix = "view:"

    def _cache_key(self, post_id: int) -> str:
        return f"{self.cache_prefix}{post_id}"

    def _view_key(self, post_id: int, client_ip: str) -> str:
        """Generate Redis key for tracking unique views"""
        return f"{self.view_prefix}{post_id}:{client_ip}"

    async def create_post(self, post_data: PostCreate) -> PostResponse:
        """Create a new post"""
        db_post = Post(**post_data.model_dump())
        created_post = await self.repository.create(db_post)
        posts_created.inc()
        log.info("Created post id={} title={}", created_post.id, created_post.title)

        # Convert to DTO for internal processing
        dto = PostDTO.from_model(created_post)
        return PostResponse(**dto.to_dict())

    async def get_post(
        self, post_id: int, client_ip: str = "unknown"
    ) -> Optional[PostResponse]:
        """Get post by ID with caching and unique view tracking"""
        cache_key = self._cache_key(post_id)

        # Try cache first; on CacheError fall back to DB
        try:
            cached = await self.cache.get(cache_key)
        except CacheError as e:
            log.warning("Cache get failed, falling back to DB: {}", e)
            cached = None
        if cached:
            cache_hits.labels(operation="get_post").inc()
            log.debug("Cache hit for post_id={}", post_id)
            asyncio.create_task(self._increment_views_in_background(post_id, client_ip))
            return PostResponse(**json.loads(cached))

        cache_misses.labels(operation="get_post").inc()
        log.debug("Cache miss for post_id={}, querying database", post_id)

        db_post = await self.repository.get_by_id(post_id)
        if not db_post:
            log.debug("Post not found: post_id={}", post_id)
            return None

        should_increment = await self._should_increment_view(post_id, client_ip)
        if should_increment:
            await self.repository.increment_views(post_id)
            posts_viewed.inc()
            log.debug("Incremented views for post_id={} from ip={}", post_id, client_ip)
            # Fetch fresh data after increment
            db_post = await self.repository.get_by_id(post_id)
            if not db_post:
                log.error("Post disappeared after increment: post_id={}", post_id)
                return None

        # Convert to DTO for internal processing
        dto = PostDTO.from_model(db_post)
        post_response = PostResponse(**dto.to_dict())

        # Store in cache; on failure log and still return response
        try:
            await self.cache.set(cache_key, post_response.model_dump_json())
            log.debug("Cached post_id={} with TTL={}s", post_id, self.cache.ttl)
        except CacheError as e:
            log.warning("Cache set failed after DB read: {}", e)

        return post_response

    async def _should_increment_view(self, post_id: int, client_ip: str) -> bool:
        """Check if view should be counted (once per IP per 24h).
        On cache error, skip increment."""
        view_key = self._view_key(post_id, client_ip)
        try:
            exists = await self.cache.exists(view_key)
            if not exists:
                await self.cache.set_with_expiry(view_key, "1", 86400)  # 24 hours
                return True
            return False
        except CacheError as e:
            log.warning("Cache error in view tracking, skipping increment: {}", e)
            return False

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
                repo = PostRepository(session)
                await repo.increment_views(post_id)

            try:
                await self.cache.delete(self._cache_key(post_id))
            except CacheError as e:
                log.warning("Cache delete failed after view increment: {}", e)
            log.debug(
                "Background view increment for post_id={} from ip={}",
                post_id,
                client_ip,
            )
        except CacheError as e:
            log.warning("Cache error in background view increment: {}", e)
        except Exception as e:
            log.error(
                "Unexpected error incrementing views for post_id={}: {}", post_id, e
            )

    async def update_post(
        self, post_id: int, post_data: PostUpdate
    ) -> Optional[PostResponse]:
        """Update post and invalidate cache"""
        db_post = await self.repository.get_by_id(post_id)
        if not db_post:
            log.debug("Update failed: post_id={} not found", post_id)
            return None

        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)

        updated_post = await self.repository.update(db_post)

        try:
            await self.cache.delete(self._cache_key(post_id))
            log.info("Updated post_id={}, invalidated cache", post_id)
        except CacheError as e:
            log.warning("Cache invalidation failed after update: {}", e)

        # Convert to DTO for internal processing
        dto = PostDTO.from_model(updated_post)
        return PostResponse(**dto.to_dict())

    async def delete_post(self, post_id: int) -> bool:
        """Delete post and invalidate cache"""
        deleted = await self.repository.delete(post_id)
        if deleted:
            try:
                await self.cache.delete(self._cache_key(post_id))
                log.info("Deleted post_id={}, invalidated cache", post_id)
            except CacheError as e:
                log.warning("Cache invalidation failed after delete: {}", e)
            return True

        log.debug("Delete failed: post_id={} not found", post_id)
        return False

    async def get_all_posts(
        self, skip: int = 0, limit: int = 100
    ) -> list[PostResponse]:
        """Get all posts with pagination"""
        posts = await self.repository.get_all(skip, limit)
        # Convert to DTOs for internal processing
        dtos = [PostDTO.from_model(post) for post in posts]
        return [PostResponse(**dto.to_dict()) for dto in dtos]
