import asyncio
from contextlib import asynccontextmanager
import socket
from typing import AsyncGenerator

import asyncpg
from httpx import ASGITransport
from httpx import AsyncClient
import pytest
import pytest_asyncio
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from src.blogcache.core.config import settings
from src.blogcache.core.database import Base
from src.blogcache.core.database import get_db
from src.blogcache.core.database import get_redis
from src.blogcache.main import app


def get_db_host():
    """Determine the correct database host"""
    try:
        socket.gethostbyname("postgres")
        return "postgres"
    except socket.gaierror:
        return "localhost"


def get_redis_host():
    """Determine the correct redis host"""
    db_host = get_db_host()
    return "redis" if db_host == "postgres" else "localhost"


TEST_DB_HOST = get_db_host()
TEST_REDIS_HOST = get_redis_host()

TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{TEST_DB_HOST}:5432/{settings.test_postgres_db}"
TEST_REDIS_URL = f"redis://{TEST_REDIS_HOST}:6379/{settings.test_redis_db}"


@pytest.fixture(scope="session", autouse=True)
async def ensure_test_db_exists():
    """Ensure test database exists before running tests"""
    try:
        conn = await asyncpg.connect(
            user=settings.postgres_user,
            password=settings.postgres_password,
            database="postgres",
            host=TEST_DB_HOST,
        )

        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", settings.test_postgres_db
        )

        if not exists:
            await conn.execute(f"CREATE DATABASE {settings.test_postgres_db}")

        await conn.close()
    except Exception as e:
        pytest.fail(f"Failed to connect to PostgreSQL: {e}")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database(test_engine):
    """Clean all tables before each test and reset sequences"""
    async with test_engine.begin() as conn:
        # Disable triggers temporarily to allow truncation
        await conn.execute(text("SET session_replication_role = 'replica';"))

        # Get all table names
        result = await conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
            """
            )
        )
        tables = result.scalars().all()

        # Truncate all tables
        for table in tables:
            await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))

        # Reset all sequences
        result = await conn.execute(
            text(
                """
                SELECT sequencename
                FROM pg_sequences
                WHERE schemaname = 'public'
            """
            )
        )
        sequences = result.scalars().all()

        for seq in sequences:
            await conn.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1;"))

        # Re-enable triggers
        await conn.execute(text("SET session_replication_role = 'origin';"))

    yield


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test with transaction rollback"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async with async_session() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Create Redis client for testing with automatic cleanup."""
    client = Redis.from_url(TEST_REDIS_URL, decode_responses=True)

    await client.ping()
    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture
async def client(test_engine, redis_client) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with isolated session for each test."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def override_get_db():
        async with async_session() as session:
            await session.begin()
            try:
                yield session
            finally:
                await session.rollback()
                await session.close()

    async def override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_factory(test_engine, redis_client):
    """Create a fresh client for each request with shared session"""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    @asynccontextmanager
    async def _get_client():
        async with async_session() as session:

            async def override_get_db():
                yield session

            async def override_get_redis():
                yield redis_client

            app.dependency_overrides[get_db] = override_get_db
            app.dependency_overrides[get_redis] = override_get_redis

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                yield client

            app.dependency_overrides.clear()

    return _get_client
