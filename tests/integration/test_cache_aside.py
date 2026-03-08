"""Integration tests for Cache-Aside pattern implementation."""

import asyncio

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.blogcache.models.post import Post


async def test_cache_miss_then_hit(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test Cache-Aside: first request hits DB, second hits cache."""
    post = Post(title="Test Post", content="Test Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    await redis_client.flushdb()

    # Cache miss - should query DB
    response1 = await client.get(f"/posts/{post_id}")
    assert response1.status_code == 200
    assert response1.json()["title"] == "Test Post"
    assert response1.json()["views"] == 1

    # Verify cached
    cached = await redis_client.get(f"post:{post_id}")
    assert cached is not None

    # Cache hit - should return from Redis
    response2 = await client.get(f"/posts/{post_id}")
    assert response2.status_code == 200
    assert response2.json()["views"] == 1  # Same view count

    await asyncio.sleep(0.2)


async def test_cache_invalidation_on_update(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test cache invalidation when post is updated."""
    post = Post(title="Original", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    # Populate cache
    await client.get(f"/posts/{post_id}")
    assert await redis_client.get(f"post:{post_id}") is not None

    # Update should invalidate cache
    response = await client.put(f"/posts/{post_id}", json={"title": "Updated"})
    assert response.status_code == 200
    assert await redis_client.get(f"post:{post_id}") is None

    # Next GET should repopulate cache
    response = await client.get(f"/posts/{post_id}")
    assert response.json()["title"] == "Updated"
    assert await redis_client.get(f"post:{post_id}") is not None

    await asyncio.sleep(0.2)


async def test_cache_invalidation_on_delete(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test cache invalidation when post is deleted."""
    post = Post(title="To Delete", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    # Populate cache
    await client.get(f"/posts/{post_id}")
    assert await redis_client.get(f"post:{post_id}") is not None

    # Delete should invalidate cache
    response = await client.delete(f"/posts/{post_id}")
    assert response.status_code == 204
    assert await redis_client.get(f"post:{post_id}") is None

    # Verify post is gone
    response = await client.get(f"/posts/{post_id}")
    assert response.status_code == 404

    await asyncio.sleep(0.2)


async def test_cache_ttl(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that cache entries have TTL set."""
    post = Post(title="TTL Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    await client.get(f"/posts/{post_id}")

    ttl = await redis_client.ttl(f"post:{post_id}")
    assert 0 < ttl <= 300  # Between 0 and 5 minutes

    await asyncio.sleep(0.2)


async def test_redis_failure_fallback(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Test that app falls back to DB when Redis fails."""
    from redis.asyncio import Redis

    post = Post(title="Fallback Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    async def mock_redis_get(*args, **kwargs):
        raise Exception("Redis unavailable")

    monkeypatch.setattr(Redis, "get", mock_redis_get)

    # Should still work via DB fallback
    response = await client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Fallback Test"
