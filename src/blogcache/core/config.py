from typing import Annotated

from pydantic import Field
from pydantic import computed_field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    app_name: Annotated[str, Field(description="Application name")] = "blogcache"
    debug: Annotated[bool, Field(description="Debug mode")] = True
    secret_key: Annotated[str, Field(description="Secret key for security")] = (
        "dev-secret-key-change-in-production"
    )

    postgres_user: Annotated[str, Field(description="PostgreSQL username")] = "postgres"
    postgres_password: Annotated[str, Field(description="PostgreSQL password")] = (
        "postgres"
    )
    postgres_db: Annotated[str, Field(description="PostgreSQL database name")] = (
        "blogcache"
    )
    postgres_host: Annotated[str, Field(description="PostgreSQL host")] = "localhost"
    postgres_port: Annotated[int, Field(description="PostgreSQL port")] = 5432

    redis_host: Annotated[str, Field(description="Redis host")] = "localhost"
    redis_port: Annotated[int, Field(description="Redis port")] = 6379
    redis_db: Annotated[int, Field(description="Redis database number")] = 0

    test_postgres_db: Annotated[str, Field(description="Test database name")] = (
        "blogcache_test"
    )
    test_redis_db: Annotated[int, Field(description="Test Redis database number")] = 1

    @computed_field
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field
    @property
    def test_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.test_postgres_db}"

    @computed_field
    @property
    def test_redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.test_redis_db}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


settings = Settings()
