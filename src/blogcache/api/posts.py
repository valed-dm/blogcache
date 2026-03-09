from typing import Annotated
from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.database import get_redis
from ..core.exceptions import PostNotFoundError
from ..core.rate_limit import limiter
from ..schemas.post import PostCreate
from ..schemas.post import PostResponse
from ..schemas.post import PostUpdate
from ..services.post_service import PostService


router = APIRouter(prefix="/posts", tags=["posts"])


async def get_post_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> PostService:
    return PostService(db, redis)


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_post(
    request: Request,
    post_data: PostCreate,
    service: Annotated[PostService, Depends(get_post_service)],
) -> PostResponse:
    """Create a new blog post (rate limited: 10/minute)."""
    return await service.create_post(post_data)


@router.get("/", response_model=List[PostResponse])
async def read_posts(
    service: Annotated[PostService, Depends(get_post_service)],
    skip: int = 0,
    limit: int = 100,
) -> List[PostResponse]:
    """Get all posts with pagination"""
    return await service.get_all_posts(skip=skip, limit=limit)


@router.get("/{post_id}", response_model=PostResponse)
async def read_post(
    post_id: int,
    request: Request,
    service: Annotated[PostService, Depends(get_post_service)],
) -> PostResponse:
    """Get post by ID (with caching and unique view tracking)"""
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "unknown"

    post = await service.get_post(post_id, client_ip)
    if not post:
        raise PostNotFoundError(post_id)
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    service: Annotated[PostService, Depends(get_post_service)],
) -> PostResponse:
    """Update post and invalidate cache"""
    post = await service.update_post(post_id, post_data)
    if not post:
        raise PostNotFoundError(post_id)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    service: Annotated[PostService, Depends(get_post_service)],
) -> None:
    """Delete post and invalidate cache"""
    deleted = await service.delete_post(post_id)
    if not deleted:
        raise PostNotFoundError(post_id)
    return None
