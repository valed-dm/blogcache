"""Integration tests for API endpoints and application behavior."""

from httpx import AsyncClient


async def test_health_check(client: AsyncClient):
    """Test GET /health returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "blogcache"


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
