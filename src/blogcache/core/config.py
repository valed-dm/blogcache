from typing import Annotated

from pydantic import Field
from pydantic import computed_field
from pydantic import model_validator
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def test_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.test_postgres_db}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def test_redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.test_redis_db}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @model_validator(mode="after")
    def validate_config(self) -> "Settings":
        """Validate configuration after initialization.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If configuration is invalid.
        """
        from loguru import logger

        # Warn about default secret key in debug mode
        if self.debug and "change-in-production" in self.secret_key:
            logger.warning(
                "Using default SECRET_KEY in debug mode - change for production!"
            )

        # Fail fast if default secret key in production
        if not self.debug and "change-in-production" in self.secret_key:
            raise ValueError(
                "SECRET_KEY must be changed in production! "
                "Set SECRET_KEY environment variable."
            )

        # Validate database connection parameters
        if not self.postgres_host:
            raise ValueError("POSTGRES_HOST cannot be empty")

        if not self.postgres_db:
            raise ValueError("POSTGRES_DB cannot be empty")

        # Validate Redis connection parameters
        if not self.redis_host:
            raise ValueError("REDIS_HOST cannot be empty")

        if self.redis_port < 1 or self.redis_port > 65535:
            raise ValueError(
                f"REDIS_PORT must be between 1-65535, got {self.redis_port}"
            )

        return self


settings = Settings()
