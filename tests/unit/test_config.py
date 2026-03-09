"""Unit tests for configuration validation."""

import pytest


def test_config_validates_secret_key_in_production(monkeypatch):
    """Test that default secret key raises error in production."""
    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("SECRET_KEY", "dev-secret-key-change-in-production")

    with pytest.raises(ValueError, match="SECRET_KEY must be changed in production"):
        from src.blogcache.core.config import Settings

        Settings()


def test_config_allows_default_secret_in_debug(monkeypatch):
    """Test that default secret key is allowed in debug mode."""
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("SECRET_KEY", "dev-secret-key-change-in-production")

    from src.blogcache.core.config import Settings

    settings = Settings()
    assert settings.debug is True
    assert "change-in-production" in settings.secret_key


def test_config_validates_postgres_host(monkeypatch):
    """Test that empty postgres host raises error."""
    monkeypatch.setenv("POSTGRES_HOST", "")

    with pytest.raises(ValueError, match="POSTGRES_HOST cannot be empty"):
        from src.blogcache.core.config import Settings

        Settings()


def test_config_validates_postgres_db(monkeypatch):
    """Test that empty postgres db raises error."""
    monkeypatch.setenv("POSTGRES_DB", "")

    with pytest.raises(ValueError, match="POSTGRES_DB cannot be empty"):
        from src.blogcache.core.config import Settings

        Settings()


def test_config_validates_redis_host(monkeypatch):
    """Test that empty redis host raises error."""
    monkeypatch.setenv("REDIS_HOST", "")

    with pytest.raises(ValueError, match="REDIS_HOST cannot be empty"):
        from src.blogcache.core.config import Settings

        Settings()


def test_config_validates_redis_port_range(monkeypatch):
    """Test that invalid redis port raises error."""
    monkeypatch.setenv("REDIS_PORT", "99999")

    with pytest.raises(ValueError, match="REDIS_PORT must be between 1-65535"):
        from src.blogcache.core.config import Settings

        Settings()
