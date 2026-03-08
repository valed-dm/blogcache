"""Integration tests for API input validation."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.blogcache.models.post import Post


async def test_create_post_empty_title(client: AsyncClient):
    """Test POST /posts/ rejects empty title."""
    response = await client.post("/posts/", json={"title": "", "content": "Content"})
    assert response.status_code == 422


async def test_create_post_empty_content(client: AsyncClient):
    """Test POST /posts/ rejects empty content."""
    response = await client.post("/posts/", json={"title": "Title", "content": ""})
    assert response.status_code == 422


async def test_create_post_title_too_long(client: AsyncClient):
    """Test POST /posts/ rejects title exceeding max length."""
    response = await client.post(
        "/posts/", json={"title": "x" * 300, "content": "Content"}
    )
    assert response.status_code == 422


async def test_create_post_missing_fields(client: AsyncClient):
    """Test POST /posts/ rejects missing required fields."""
    response = await client.post("/posts/", json={"title": "Title"})
    assert response.status_code == 422


async def test_update_post_empty_data(client: AsyncClient, db_session: AsyncSession):
    """Test PUT /posts/{id} with empty data does nothing."""
    post = Post(title="Original", content="Original Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await client.put(f"/posts/{post.id}", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original"
    assert data["content"] == "Original Content"


async def test_update_post_title_too_long(
    client: AsyncClient, db_session: AsyncSession
):
    """Test PUT /posts/{id} rejects title exceeding max length."""
    post = Post(title="Original", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await client.put(f"/posts/{post.id}", json={"title": "x" * 300})
    assert response.status_code == 422


async def test_invalid_post_id_format(client: AsyncClient):
    """Test that invalid post ID format returns 422."""
    response = await client.get("/posts/invalid")
    assert response.status_code == 422
