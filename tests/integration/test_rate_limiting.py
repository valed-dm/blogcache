"""Integration tests for rate limiting."""

from httpx import AsyncClient


async def test_rate_limit_create_post(client: AsyncClient):
    """Test that create post endpoint is rate limited."""
    # Make 11 requests (limit is 10/minute)
    responses = []
    for i in range(11):
        response = await client.post(
            "/posts/",
            json={"title": f"Test Post {i}", "content": f"Content {i}"},
        )
        responses.append(response)

    # At least one should be rate limited (429)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)
    assert rate_limited_count >= 1, "Expected at least one rate limited response"

    # Check rate limit response format
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    if rate_limited_responses:
        assert "rate limit" in rate_limited_responses[0].text.lower()
