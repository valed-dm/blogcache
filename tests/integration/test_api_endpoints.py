"""Integration tests for API endpoints and application behavior."""

from httpx import AsyncClient


async def test_health_check(client: AsyncClient, monkeypatch):
    """Test GET /health returns healthy status with detailed checks."""
    from src.blogcache.core.health import HealthCheckService

    # Mock health checks to avoid connecting to main database
    async def mock_check_postgres(*args, **kwargs):
        return True

    async def mock_check_redis(*args, **kwargs):
        return True

    monkeypatch.setattr(HealthCheckService, "check_postgres", mock_check_postgres)
    monkeypatch.setattr(HealthCheckService, "check_redis", mock_check_redis)

    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "blogcache"
    assert data["version"] == "0.1.0"
    assert "checks" in data
    assert data["checks"]["postgres"] == "healthy"
    assert data["checks"]["redis"] == "healthy"


async def test_root_redirect_to_docs(client: AsyncClient):
    """Test GET / redirects to /docs."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/docs" in response.headers["location"]


async def test_openapi_docs_available(client: AsyncClient):
    """Test that OpenAPI documentation is accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200


async def test_openapi_json_available(client: AsyncClient):
    """Test that OpenAPI JSON schema is accessible."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data


async def test_health_check_unhealthy_redis(client: AsyncClient, monkeypatch):
    """Test health check returns 503 when Redis is down."""
    from src.blogcache.core.health import HealthCheckService

    async def mock_check_redis(*args, **kwargs):
        return False

    monkeypatch.setattr(HealthCheckService, "check_redis", mock_check_redis)

    response = await client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["checks"]["redis"] == "unhealthy"


async def test_metrics_endpoint(client: AsyncClient):
    """Test that Prometheus metrics endpoint is accessible."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    content = response.text
    # Check for some expected metrics
    assert "blogcache_cache_hits_total" in content
    assert "blogcache_cache_misses_total" in content
    assert "blogcache_posts_created_total" in content
