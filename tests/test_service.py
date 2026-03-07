from src.blogcache.schemas.post import PostCreate
from src.blogcache.schemas.post import PostUpdate
from src.blogcache.services.post_service import PostService


async def test_service_create_post(db_session, redis_client):
    """Test PostService.create_post directly"""
    service = PostService(db_session, redis_client)
    post_data = PostCreate(title="Service Test", content="Service Content")

    result = await service.create_post(post_data)
    assert result.title == "Service Test"
    assert result.views == 0


async def test_service_get_post_not_found(db_session, redis_client):
    """Test PostService.get_post with non-existent post"""
    service = PostService(db_session, redis_client)
    result = await service.get_post(99999)
    assert result is None


async def test_service_update_post_not_found(db_session, redis_client):
    """Test PostService.update_post with non-existent post"""
    service = PostService(db_session, redis_client)
    result = await service.update_post(99999, PostUpdate(title="New"))
    assert result is None


async def test_service_delete_post_not_found(db_session, redis_client):
    """Test PostService.delete_post with non-existent post"""
    service = PostService(db_session, redis_client)
    result = await service.delete_post(99999)
    assert result is False


async def test_service_increment_views_error_handling(
    db_session, redis_client, monkeypatch
):
    """Test error handling in _increment_views_in_background"""
    from src.blogcache.models.post import Post

    post = Post(title="Error Test", content="Test", views=0)
    db_session.add(post)
    await db_session.commit()
    await db_session.refresh(post)

    service = PostService(db_session, redis_client)

    # Mock execute to raise exception
    async def mock_execute(*args, **kwargs):
        raise Exception("DB Error")

    monkeypatch.setattr(db_session, "execute", mock_execute)

    # This should not raise exception (it's caught internally)
    await service._increment_views_in_background(post.id)
    # If we get here, test passes
