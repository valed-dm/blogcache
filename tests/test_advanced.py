import asyncio

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.blogcache.models.post import Post


async def test_create_post_with_empty_content(client: AsyncClient):
    """Test creating post with empty content (should fail validation)"""
    post_data = {
        "title": "Test Post",
        "content": "",
    }
    response = await client.post("/posts/", json=post_data)
    assert response.status_code == 422


async def test_create_post_with_too_long_title(client: AsyncClient):
    """Test creating post with title too long"""
    post_data = {
        "title": "x" * 300,
        "content": "Valid content",
    }
    response = await client.post("/posts/", json=post_data)
    assert response.status_code == 422


async def test_update_post_partial(client: AsyncClient, db_session: AsyncSession):
    """Test partial update of post (only title)"""
    post = Post(title="Original Title", content="Original Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    update_data = {"title": "Updated Title"}
    response = await client.put(f"/posts/{post_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Original Content"


async def test_update_post_with_empty_data(
    client: AsyncClient, db_session: AsyncSession
):
    """Test update with empty data (should do nothing)"""
    post = Post(title="Original Title", content="Original Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    update_data = {}
    response = await client.put(f"/posts/{post_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original Title"
    assert data["content"] == "Original Content"


async def test_delete_nonexistent_post(client: AsyncClient):
    """Test deleting a post that doesn't exist"""
    response = await client.delete("/posts/99999")
    assert response.status_code == 404


async def test_get_posts_pagination(client: AsyncClient, db_session: AsyncSession):
    """Test pagination for get all posts"""
    for i in range(5):
        post = Post(title=f"Post {i}", content=f"Content {i}", views=0)
        db_session.add(post)
    await db_session.commit()

    # Test default pagination (skip=0, limit=100)
    response = await client.get("/posts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5

    # Test with skip and limit
    response = await client.get("/posts/?skip=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "blogcache"


async def test_root_redirect(client: AsyncClient):
    """Test root redirect to docs"""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/docs" in response.headers["location"]


async def test_concurrent_requests(test_engine, redis_client):
    """Test concurrent unique view tracking with different IPs"""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from src.blogcache.services.post_service import PostService

    AsyncSessionLocal = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        post = Post(title="Concurrent Test", content="Test", views=0)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        post_id = post.id

    await redis_client.delete(f"post:{post_id}")

    async def make_request_with_ip(ip_suffix: int):
        async with AsyncSessionLocal() as session:
            service = PostService(session, redis_client)
            client_ip = f"192.168.1.{ip_suffix}"
            result = await service.get_post(post_id, client_ip)
            return result

    tasks = [make_request_with_ip(i) for i in range(1, 11)]
    results = await asyncio.gather(*tasks)

    for result in results:
        assert result is not None
        assert result.id == post_id

    await asyncio.sleep(0.2)

    async with AsyncSessionLocal() as session:
        service = PostService(session, redis_client)
        final_result = await service.get_post(post_id, "192.168.1.100")
        assert final_result is not None
        assert final_result.views >= 10


async def test_unique_view_tracking(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that same IP doesn't increment views multiple times"""
    post = Post(title="Unique View Test", content="Test", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    await redis_client.flushdb()

    response1 = await client.get(f"/posts/{post_id}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["views"] == 1

    await asyncio.sleep(0.2)

    response2 = await client.get(f"/posts/{post_id}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["views"] == 1

    response3 = await client.get(f"/posts/{post_id}")
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["views"] == 1


async def test_cache_expiry(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that cache expires after TTL"""
    post = Post(title="TTL Test", content="Test", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    # First request - cache miss
    response1 = await client.get(f"/posts/{post_id}")
    assert response1.status_code == 200

    # Verify in cache
    cached = await redis_client.get(f"post:{post_id}")
    assert cached is not None

    # Test that TTL is set
    ttl = await redis_client.ttl(f"post:{post_id}")
    assert ttl > 0
    assert ttl <= 300  # Max 5 minutes


async def test_redis_connection_failure(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Test behavior when Redis is unavailable"""
    from redis.asyncio import Redis

    post = Post(title="Redis Failure Test", content="Test", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    async def mock_redis_get(*args, **kwargs):
        raise Exception("Redis connection failed")

    monkeypatch.setattr(Redis, "get", mock_redis_get)

    # Request should still work (fallback to DB)
    response = await client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Redis Failure Test"
