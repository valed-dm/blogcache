from typing import Annotated
from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.database import get_redis
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
async def create_post(
    post_data: PostCreate,
    service: Annotated[PostService, Depends(get_post_service)],
):
    """Create a new blog post"""
    return await service.create_post(post_data)


@router.get("/", response_model=List[PostResponse])
async def read_posts(
    service: Annotated[PostService, Depends(get_post_service)],
    skip: int = 0,
    limit: int = 100,
):
    """Get all posts with pagination"""
    return await service.get_all_posts(skip=skip, limit=limit)


@router.get("/{post_id}", response_model=PostResponse)
async def read_post(
    post_id: int,
    request: Request,
    service: Annotated[PostService, Depends(get_post_service)],
):
    """Get post by ID (with caching and unique view tracking)"""
    client_ip = request.client.host if request.client else "unknown"
    post = await service.get_post(post_id, client_ip)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    service: Annotated[PostService, Depends(get_post_service)],
):
    """Update post and invalidate cache"""
    post = await service.update_post(post_id, post_data)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    service: Annotated[PostService, Depends(get_post_service)],
):
    """Delete post and invalidate cache"""
    deleted = await service.delete_post(post_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return None
