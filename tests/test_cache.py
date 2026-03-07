import asyncio

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.blogcache.models.post import Post


async def test_cache_hit_and_miss(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """
    Test that first request goes to DB (cache miss) and second
    comes from cache (cache hit).
    """
    post = Post(title="Test Post", content="Test Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    await redis_client.flushdb()

    response1 = await client.get(f"/posts/{post_id}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["title"] == "Test Post"
    assert data1["views"] == 1

    cached = await redis_client.get(f"post:{post_id}")
    assert cached is not None

    response2 = await client.get(f"/posts/{post_id}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["views"] == 1

    await asyncio.sleep(0.2)


async def test_cache_invalidation_on_update(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that updating a post removes it from cache."""
    post = Post(title="Original Title", content="Original Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    await client.get(f"/posts/{post_id}")

    cached_before = await redis_client.get(f"post:{post_id}")
    assert cached_before is not None
    assert "Original Title" in cached_before

    update_response = await client.put(
        f"/posts/{post_id}", json={"title": "Updated Title"}
    )
    assert update_response.status_code == 200

    cached_after = await redis_client.get(f"post:{post_id}")
    assert cached_after is None

    get_response = await client.get(f"/posts/{post_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Updated Title"

    cached_final = await redis_client.get(f"post:{post_id}")
    assert cached_final is not None
    assert "Updated Title" in cached_final

    await asyncio.sleep(0.2)


async def test_cache_invalidation_on_delete(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that deleting a post removes it from cache."""
    post = Post(title="To Delete", content="Will be deleted", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    await client.get(f"/posts/{post_id}")

    cached_before = await redis_client.get(f"post:{post_id}")
    assert cached_before is not None

    delete_response = await client.delete(f"/posts/{post_id}")
    assert delete_response.status_code == 204

    cached_after = await redis_client.get(f"post:{post_id}")
    assert cached_after is None

    get_response = await client.get(f"/posts/{post_id}")
    assert get_response.status_code == 404

    await asyncio.sleep(0.2)


async def test_cache_ttl(
    client: AsyncClient, db_session: AsyncSession, redis_client: Redis
):
    """Test that cache entries expire after TTL."""
    post = Post(title="TTL Test", content="Will expire", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    post_id = post.id

    await client.get(f"/posts/{post_id}")

    ttl = await redis_client.ttl(f"post:{post_id}")
    assert ttl > 0

    await asyncio.sleep(0.2)


async def test_get_nonexistent_post(client: AsyncClient):
    """Test that getting a non-existent post returns 404."""
    response = await client.get("/posts/99999")
    assert response.status_code == 404


async def test_create_post_api(client: AsyncClient):
    """Test post creation via API."""
    post_data = {
        "title": "API Created Post",
        "content": "This post was created via API",
    }

    response = await client.post("/posts/", json=post_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == post_data["title"]
    assert data["content"] == post_data["content"]
    assert data["id"] is not None
    assert data["views"] == 0
