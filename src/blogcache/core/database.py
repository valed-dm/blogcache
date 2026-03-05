from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings


# SQLAlchemy
engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


# Redis
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_db() -> AsyncSession:
    """Dependency for getting DB session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> Redis:
    """Dependency for getting Redis client"""
    return redis_client
