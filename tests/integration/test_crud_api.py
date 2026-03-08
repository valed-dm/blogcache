"""Integration tests for CRUD operations via REST API."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.blogcache.models.post import Post


async def test_create_post(client: AsyncClient):
    """Test POST /posts/ creates a new post."""
    response = await client.post(
        "/posts/", json={"title": "New Post", "content": "New Content"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Post"
    assert data["content"] == "New Content"
    assert data["id"] is not None
    assert data["views"] == 0


async def test_get_post(client: AsyncClient, db_session: AsyncSession):
    """Test GET /posts/{id} retrieves a post."""
    post = Post(title="Get Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await client.get(f"/posts/{post.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Test"


async def test_get_nonexistent_post(client: AsyncClient):
    """Test GET /posts/{id} returns 404 for missing post."""
    response = await client.get("/posts/99999")
    assert response.status_code == 404


async def test_update_post(client: AsyncClient, db_session: AsyncSession):
    """Test PUT /posts/{id} updates a post."""
    post = Post(title="Original", content="Original Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await client.put(
        f"/posts/{post.id}", json={"title": "Updated", "content": "Updated Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["content"] == "Updated Content"


async def test_update_post_partial(client: AsyncClient, db_session: AsyncSession):
    """Test PUT /posts/{id} with partial data updates only specified fields."""
    post = Post(title="Original", content="Original Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    response = await client.put(f"/posts/{post.id}", json={"title": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["content"] == "Original Content"


async def test_update_nonexistent_post(client: AsyncClient):
    """Test PUT /posts/{id} returns 404 for missing post."""
    response = await client.put("/posts/99999", json={"title": "Updated"})
    assert response.status_code == 404


async def test_delete_post(client: AsyncClient, db_session: AsyncSession):
    """Test DELETE /posts/{id} removes a post."""
    post = Post(title="To Delete", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)
    post_id = post.id

    response = await client.delete(f"/posts/{post_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(f"/posts/{post_id}")
    assert response.status_code == 404


async def test_delete_nonexistent_post(client: AsyncClient):
    """Test DELETE /posts/{id} returns 404 for missing post."""
    response = await client.delete("/posts/99999")
    assert response.status_code == 404


async def test_list_posts(client: AsyncClient, db_session: AsyncSession):
    """Test GET /posts/ returns list of posts."""
    for i in range(3):
        post = Post(title=f"Post {i}", content=f"Content {i}", views=0)
        db_session.add(post)
    await db_session.commit()

    response = await client.get("/posts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


async def test_list_posts_pagination(client: AsyncClient, db_session: AsyncSession):
    """Test GET /posts/ with skip and limit parameters."""
    for i in range(5):
        post = Post(title=f"Post {i}", content=f"Content {i}", views=0)
        db_session.add(post)
    await db_session.commit()

    response = await client.get("/posts/?skip=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
