# Test Suite Documentation

## Overview
This test suite is organized into **Integration Tests** and **Unit Tests** to clearly separate concerns and strengthen test coverage for the blogcache API.

**Test Coverage:** 86% (25+ tests)

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures (DB, Redis, HTTP client)
├── integration/                   # Tests requiring external dependencies
│   ├── test_cache_aside.py       # Cache-Aside pattern with Redis + PostgreSQL
│   ├── test_crud_api.py          # CRUD operations via REST API
│   ├── test_atomic_views.py     # Atomic view counter & race conditions
│   ├── test_validation_api.py   # Input validation via API
│   └── test_api_endpoints.py    # Health check, docs, root redirect
└── unit/                          # Tests for isolated business logic
    ├── test_schemas.py           # Pydantic schema validation
    └── test_post_service.py      # PostService business logic

```

## Integration Tests (tests/integration/)

Integration tests verify the **entire system working together** with real dependencies (PostgreSQL, Redis, FastAPI).

### test_cache_aside.py
**Purpose:** Validate Cache-Aside pattern implementation

**Key Tests:**
- `test_cache_miss_then_hit` — First request hits DB, second hits cache
- `test_cache_invalidation_on_update` — Cache cleared on POST update
- `test_cache_invalidation_on_delete` — Cache cleared on DELETE
- `test_cache_ttl` — Verify TTL is set (5 minutes)
- `test_redis_failure_fallback` — App works when Redis is down

**Why Integration:** Requires Redis + PostgreSQL + FastAPI working together

---

### test_crud_api.py
**Purpose:** Validate REST API CRUD operations

**Key Tests:**
- `test_create_post` — POST /posts/ creates new post
- `test_get_post` — GET /posts/{id} retrieves post
- `test_update_post` — PUT /posts/{id} updates post
- `test_update_post_partial` — Partial updates work correctly
- `test_delete_post` — DELETE /posts/{id} removes post
- `test_list_posts_pagination` — GET /posts/ with skip/limit

**Why Integration:** Tests HTTP layer + service layer + database layer

---

### test_atomic_views.py
**Purpose:** Validate atomic view counter and race condition prevention

**Key Tests:**
- `test_unique_view_tracking_same_ip` — Same IP doesn't increment views twice
- `test_concurrent_requests_atomic_counter` — 10 concurrent requests = 10 views (no race condition)
- `test_view_increment_background_task` — View increment doesn't block response

**Why Integration:** Requires PostgreSQL atomic SQL + Redis IP tracking + concurrent execution

**ACID Compliance:**
- **Atomicity:** `UPDATE posts SET views = views + 1` is atomic
- **Isolation:** Concurrent requests don't interfere
- **Consistency:** View count always accurate

---

### test_validation_api.py
**Purpose:** Validate input validation at API layer

**Key Tests:**
- `test_create_post_empty_title` — Rejects empty title (422)
- `test_create_post_title_too_long` — Rejects title > 200 chars (422)
- `test_update_post_empty_data` — Empty update does nothing
- `test_invalid_post_id_format` — Invalid ID format returns 422

**Why Integration:** Tests FastAPI validation + Pydantic schemas together

---

### test_api_endpoints.py
**Purpose:** Validate application endpoints

**Key Tests:**
- `test_health_check` — GET /health returns healthy status
- `test_root_redirect_to_docs` — GET / redirects to /docs
- `test_openapi_docs_available` — OpenAPI docs accessible

**Why Integration:** Tests FastAPI routing + application setup

---

## Unit Tests (tests/unit/)

Unit tests verify **isolated business logic** without external dependencies (mocked where needed).

### test_schemas.py
**Purpose:** Validate Pydantic schema validation rules

**Key Tests:**
- `test_post_create_valid` — Valid data passes
- `test_post_create_empty_title` — Empty title raises ValidationError
- `test_post_create_title_too_long` — Title > 200 chars raises ValidationError
- `test_post_update_partial` — Partial updates work
- `test_post_update_empty` — Empty update is valid

**Why Unit:** Tests Pydantic schemas in isolation (no DB/Redis/API)

---

### test_post_service.py
**Purpose:** Validate PostService business logic

**Key Tests:**
- `test_create_post` — Service creates post correctly
- `test_get_post_not_found` — Returns None for missing post
- `test_update_post_not_found` — Returns None for missing post
- `test_delete_post_not_found` — Returns False for missing post
- `test_increment_views_error_handling` — Errors caught gracefully

**Why Unit:** Tests service layer logic with real DB session (minimal integration)

---

## Running Tests

### Run All Tests
```bash
# With Docker
docker-compose -f docker-compose.local.yml run --rm app pytest

# Locally
poetry run pytest
```

### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Run Specific Test File
```bash
pytest tests/integration/test_cache_aside.py -v
```

### Run with Coverage
```bash
pytest --cov=src/blogcache --cov-report=html
open htmlcov/index.html
```

### Run Specific Test
```bash
pytest tests/integration/test_atomic_views.py::test_concurrent_requests_atomic_counter -v
```

---

## Test Fixtures (conftest.py)

**Shared fixtures available to all tests:**

- `test_engine` — Async SQLAlchemy engine for test database
- `db_session` — Async database session (auto-rollback after test)
- `redis_client` — Redis client (auto-cleanup after test)
- `client` — AsyncClient for HTTP requests to FastAPI app

**Fixture Scope:**
- `test_engine` — Session scope (reused across tests)
- `db_session` — Function scope (fresh session per test)
- `redis_client` — Function scope (isolated per test)
- `client` — Function scope (fresh client per test)

---

## Key Testing Patterns

### 1. Cache-Aside Pattern Testing
```python
# Verify cache miss → DB query → cache population
await redis_client.flushdb()
response = await client.get(f"/posts/{post_id}")
cached = await redis_client.get(f"post:{post_id}")
assert cached is not None
```

### 2. Race Condition Testing
```python
# Concurrent requests from different IPs
tasks = [make_request(f"192.168.1.{i}") for i in range(10)]
results = await asyncio.gather(*tasks)
# Verify atomic increment: 10 requests = 10 views
```

### 3. Cache Invalidation Testing
```python
# Populate cache
await client.get(f"/posts/{post_id}")
# Update post
await client.put(f"/posts/{post_id}", json={"title": "New"})
# Verify cache cleared
assert await redis_client.get(f"post:{post_id}") is None
```

### 4. Error Handling Testing
```python
# Mock Redis failure
monkeypatch.setattr(Redis, "get", mock_redis_get)
# Verify fallback to DB
response = await client.get(f"/posts/{post_id}")
assert response.status_code == 200
```

---

## CI/CD Integration

Tests run automatically in GitHub Actions:

```yaml
# .github/workflows/api-tests.yml
- name: Run tests
  run: |
    docker compose run --rm app pytest --cov=src/blogcache
```

**Newman/Postman tests** also run in CI (17 requests, 38 assertions).

---

## Test Philosophy

### Integration Tests Should:
✅ Test multiple components together
✅ Use real dependencies (PostgreSQL, Redis)
✅ Verify end-to-end behavior
✅ Test API contracts
✅ Validate ACID properties

### Unit Tests Should:
✅ Test single components in isolation
✅ Mock external dependencies when needed
✅ Be fast and deterministic
✅ Focus on business logic
✅ Test edge cases

---

## Adding New Tests

### Integration Test Template
```python
async def test_new_feature(client: AsyncClient, db_session: AsyncSession, redis_client: Redis):
    """Test description."""
    # Setup
    post = Post(title="Test", content="Content", views=0)
    db_session.add(post)
    await db_session.commit()

    # Execute
    response = await client.get(f"/posts/{post.id}")

    # Assert
    assert response.status_code == 200
```

### Unit Test Template
```python
def test_schema_validation():
    """Test description."""
    # Execute & Assert
    with pytest.raises(ValidationError):
        PostCreate(title="", content="Content")
```

---

## Troubleshooting

### Tests Fail with "Database not found"
```bash
# Ensure PostgreSQL is running
docker-compose -f docker-compose.local.yml up postgres -d
```

### Tests Fail with "Redis connection refused"
```bash
# Ensure Redis is running
docker-compose -f docker-compose.local.yml up redis -d
```

### Flaky Tests (Race Conditions)
```python
# Add sleep to wait for background tasks
await asyncio.sleep(0.2)
```

### Coverage Not Updating
```bash
# Clear coverage cache
rm -rf .coverage htmlcov/
pytest --cov=src/blogcache --cov-report=html
```

---

## Performance Benchmarks

**Integration Tests:** ~5-10 seconds (with Docker)
**Unit Tests:** <1 second
**Total Test Suite:** ~10 seconds

**Optimization Tips:**
- Use `pytest-xdist` for parallel execution: `pytest -n auto`
- Run unit tests first for fast feedback
- Use `--lf` flag to run last failed tests: `pytest --lf`
