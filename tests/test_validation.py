from pydantic import ValidationError
import pytest

from src.blogcache.schemas.post import PostCreate
from src.blogcache.schemas.post import PostUpdate


def test_post_create_validation():
    """Test PostCreate schema validation"""
    post = PostCreate(title="Valid Title", content="Valid Content")
    assert post.title == "Valid Title"
    assert post.content == "Valid Content"

    # Title too short
    with pytest.raises(ValidationError):
        PostCreate(title="", content="Content")

    # Title too long
    with pytest.raises(ValidationError):
        PostCreate(title="x" * 300, content="Content")

    # Content too short
    with pytest.raises(ValidationError):
        PostCreate(title="Title", content="")


def test_post_update_validation():
    """Test PostUpdate schema validation"""
    # Valid partial update
    post = PostUpdate(title="New Title")
    assert post.title == "New Title"
    assert post.content is None

    # Valid full update
    post = PostUpdate(title="New Title", content="New Content")
    assert post.title == "New Title"
    assert post.content == "New Content"

    # Invalid title length
    with pytest.raises(ValidationError):
        PostUpdate(title="x" * 300)
