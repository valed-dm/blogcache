"""Unit tests for PostDTO."""

from datetime import datetime

from src.blogcache.dto.post_dto import PostDTO
from src.blogcache.models.post import Post


def test_post_dto_from_model():
    """Test creating PostDTO from Post model."""
    post = Post(
        id=1,
        title="Test Post",
        content="Test Content",
        views=10,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0),
    )

    dto = PostDTO.from_model(post)

    assert dto.id == 1
    assert dto.title == "Test Post"
    assert dto.content == "Test Content"
    assert dto.views == 10
    assert dto.created_at == datetime(2024, 1, 1, 12, 0, 0)
    assert dto.updated_at == datetime(2024, 1, 2, 12, 0, 0)


def test_post_dto_to_dict():
    """Test converting PostDTO to dictionary."""
    dto = PostDTO(
        id=1,
        title="Test Post",
        content="Test Content",
        views=10,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 2, 12, 0, 0),
    )

    result = dto.to_dict()

    assert result["id"] == 1
    assert result["title"] == "Test Post"
    assert result["content"] == "Test Content"
    assert result["views"] == 10
    assert result["created_at"] == datetime(2024, 1, 1, 12, 0, 0)
    assert result["updated_at"] == datetime(2024, 1, 2, 12, 0, 0)
