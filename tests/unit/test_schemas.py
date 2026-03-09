"""Unit tests for Pydantic schema validation."""

from pydantic import ValidationError
import pytest

from src.blogcache.schemas.post import PostCreate
from src.blogcache.schemas.post import PostUpdate


def test_post_create_valid():
    """Test PostCreate with valid data."""
    post = PostCreate(title="Valid Title", content="Valid Content")
    assert post.title == "Valid Title"
    assert post.content == "Valid Content"


def test_post_create_empty_title():
    """Test PostCreate rejects empty title."""
    with pytest.raises(ValidationError):
        PostCreate(title="", content="Content")


def test_post_create_title_too_long():
    """Test PostCreate rejects title exceeding max length."""
    with pytest.raises(ValidationError):
        PostCreate(title="x" * 300, content="Content")


def test_post_create_empty_content():
    """Test PostCreate rejects empty content."""
    with pytest.raises(ValidationError):
        PostCreate(title="Title", content="")


def test_post_update_partial():
    """Test PostUpdate with partial data."""
    post = PostUpdate(title="New Title")
    assert post.title == "New Title"
    assert post.content is None


def test_post_update_full():
    """Test PostUpdate with all fields."""
    post = PostUpdate(title="New Title", content="New Content")
    assert post.title == "New Title"
    assert post.content == "New Content"


def test_post_update_title_too_long():
    """Test PostUpdate rejects title exceeding max length."""
    with pytest.raises(ValidationError):
        PostUpdate(title="x" * 300)


def test_post_update_empty():
    """Test PostUpdate allows empty update."""
    post = PostUpdate()
    assert post.title is None
    assert post.content is None
