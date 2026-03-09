"""Unit tests for PostService business logic."""

from src.blogcache.schemas.post import PostCreate
from src.blogcache.schemas.post import PostUpdate
from src.blogcache.services.post_service import PostService


async def test_create_post(db_session, redis_client):
    """Test PostService.create_post creates a new post."""
    service = PostService(db_session, redis_client)
    post_data = PostCreate(title="Service Test", content="Service Content")

    result = await service.create_post(post_data)
    assert result.title == "Service Test"
    assert result.content == "Service Content"
    assert result.views == 0
    assert result.id is not None


async def test_get_post_not_found(db_session, redis_client):
    """Test PostService.get_post returns None for non-existent post."""
    service = PostService(db_session, redis_client)
    result = await service.get_post(99999, "127.0.0.1")
    assert result is None


async def test_update_post_not_found(db_session, redis_client):
    """Test PostService.update_post returns None for non-existent post."""
    service = PostService(db_session, redis_client)
    result = await service.update_post(99999, PostUpdate(title="New"))
    assert result is None


async def test_delete_post_not_found(db_session, redis_client):
    """Test PostService.delete_post returns False for non-existent post."""
    service = PostService(db_session, redis_client)
    result = await service.delete_post(99999)
    assert result is False


async def test_increment_views_error_handling(db_session, redis_client, monkeypatch):
    """Test error handling in _increment_views_in_background."""
    from src.blogcache.models.post import Post

    post = Post(title="Error Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    service = PostService(db_session, redis_client)

    # Mock execute to raise exception
    async def mock_execute(*args, **kwargs):
        raise Exception("DB Error")

    monkeypatch.setattr(db_session, "execute", mock_execute)

    # Should not raise exception (caught internally)
    await service._increment_views_in_background(post.id, "127.0.0.1")
