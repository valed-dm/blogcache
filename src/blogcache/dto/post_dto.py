"""Data Transfer Objects for internal communication.

DTOs decouple internal domain logic from API schemas,
making refactoring easier and improving maintainability.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..models.post import Post


@dataclass
class PostDTO:
    """Internal data transfer object for Post entity."""

    id: int
    title: str
    content: str
    views: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, post: Post) -> "PostDTO":
        """Create DTO from SQLAlchemy model.

        Args:
            post: Post model instance.

        Returns:
            PostDTO instance.
        """
        return cls(
            id=post.id,
            title=post.title,
            content=post.content,
            views=post.views,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "views": self.views,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
