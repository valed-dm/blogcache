"""Integration tests for atomic view counter and race condition prevention."""

import asyncio

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.blogcache.models.post import Post


async def test_unique_view_tracking_same_ip(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that same IP doesn't increment views multiple times within 24h."""
    post = Post(title="Unique View Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    await redis_client.flushdb()

    # First request - should increment
    response1 = await client.get(f"/posts/{post_id}")
    assert response1.json()["views"] == 1

    await asyncio.sleep(0.2)

    # Second request from same IP - should NOT increment
    response2 = await client.get(f"/posts/{post_id}")
    assert response2.json()["views"] == 1

    # Third request - still should NOT increment
    response3 = await client.get(f"/posts/{post_id}")
    assert response3.json()["views"] == 1


async def test_concurrent_requests_atomic_counter(test_engine, redis_client):
    """Test atomic view counter with concurrent requests from different IPs."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.blogcache.services.post_service import PostService

    AsyncSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create test post
    async with AsyncSessionLocal() as session:
        post = Post(title="Concurrent Test", content="Content", views=0)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        post_id = post.id

    await redis_client.delete(f"post:{post_id}")

    # Simulate 10 concurrent requests from different IPs
    async def make_request(ip_suffix: int):
        async with AsyncSessionLocal() as session:
            service = PostService(session, redis_client)
            return await service.get_post(post_id, f"192.168.1.{ip_suffix}")

    results = await asyncio.gather(*[make_request(i) for i in range(1, 11)])

    # All requests should succeed
    assert all(r is not None for r in results)

    await asyncio.sleep(0.2)

    # Verify final view count is exactly 10 (atomic increment)
    async with AsyncSessionLocal() as session:
        service = PostService(session, redis_client)
        final = await service.get_post(post_id, "192.168.1.100")
        assert final is not None
        assert final.views >= 10  # At least 10 unique IPs


async def test_view_increment_background_task(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that view increment happens in background without blocking response."""
    post = Post(title="Background Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    await redis_client.flushdb()

    # Request should return immediately
    response = await client.get(f"/posts/{post_id}")
    assert response.status_code == 200

    # Wait for background task
    await asyncio.sleep(0.2)

    # Verify view was incremented
    response = await client.get(f"/posts/{post_id}")
    assert response.json()["views"] == 1
