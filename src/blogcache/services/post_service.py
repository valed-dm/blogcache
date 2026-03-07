import asyncio
import json
import logging
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.post import Post
from ..schemas.post import PostCreate
from ..schemas.post import PostResponse
from ..schemas.post import PostUpdate


logger = logging.getLogger(__name__)


class PostService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.cache_prefix = "post:"
        self.cache_ttl = 300  # 5 minutes

    def _cache_key(self, post_id: int) -> str:
        return f"{self.cache_prefix}{post_id}"

    async def create_post(self, post_data: PostCreate) -> PostResponse:
        """Create a new post"""
        db_post = Post(**post_data.model_dump())
        self.db.add(db_post)
        await self.db.commit()
        await self.db.refresh(db_post)
        return PostResponse.model_validate(db_post)

    async def get_post(self, post_id: int) -> Optional[PostResponse]:
        """Get post by ID with caching (Cache-Aside pattern)"""
        try:
            cached = await self.redis.get(self._cache_key(post_id))
            if cached:
                asyncio.create_task(self._increment_views_in_background(post_id))
                return PostResponse(**json.loads(cached))
        except Exception as e:
            logger.error(f"Redis error in get_post: {e}")

        result = await self.db.execute(select(Post).where(Post.id == post_id))
        db_post = result.scalar_one_or_none()

        if not db_post:
            return None

        from sqlalchemy import text

        await self.db.execute(
            text("UPDATE posts SET views = views + 1 WHERE id = :id"),
            {"id": post_id},
        )
        await self.db.commit()
        await self.db.refresh(db_post)

        post_response = PostResponse.model_validate(db_post)
        try:
            await self.redis.setex(
                self._cache_key(post_id),
                self.cache_ttl,
                post_response.model_dump_json(),
            )
        except Exception as e:
            logger.error(f"Redis error in setex: {e}")

        return post_response

    async def _increment_views_in_background(self, post_id: int):
        """Increment views atomically using raw SQL with separate session"""
        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import async_sessionmaker

            from ..core.database import engine

            AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
                    {"id": post_id},
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Error incrementing views: {e}")

    async def update_post(
        self, post_id: int, post_data: PostUpdate
    ) -> Optional[PostResponse]:
        """Update post and invalidate cache"""
        # Get existing post
        result = await self.db.execute(select(Post).where(Post.id == post_id))
        db_post = result.scalar_one_or_none()

        if not db_post:
            return None

        # Update fields
        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)

        await self.db.commit()
        await self.db.refresh(db_post)

        # Invalidate cache
        await self.redis.delete(self._cache_key(post_id))

        return PostResponse.model_validate(db_post)

    async def delete_post(self, post_id: int) -> bool:
        """Delete post and invalidate cache"""
        result = await self.db.execute(
            delete(Post).where(Post.id == post_id).returning(Post.id)
        )
        deleted_id = result.scalar_one_or_none()

        if deleted_id:
            # Invalidate cache
            await self.redis.delete(self._cache_key(post_id))
            await self.db.commit()
            return True

        return False

    async def get_all_posts(
        self, skip: int = 0, limit: int = 100
    ) -> list[PostResponse]:
        """Get all posts with pagination"""
        result = await self.db.execute(
            select(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit)
        )
        posts = result.scalars().all()
        return [PostResponse.model_validate(post) for post in posts]
