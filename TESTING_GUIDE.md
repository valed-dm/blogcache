# Quick Testing Guide

## Test Structure

```
tests/
├── integration/    # 29 tests - Full system with DB + Redis + API
└── unit/          # 13 tests - Isolated business logic
```

## Quick Commands

```bash
# All tests (42 tests, ~14s)
pytest

# Fast feedback - unit tests only (13 tests, ~2.5s)
pytest tests/unit/ -v

# Thorough validation - integration tests only (29 tests, ~12s)
pytest tests/integration/ -v

# Specific test file
pytest tests/integration/test_cache_aside.py -v

# With coverage report
pytest --cov=src/blogcache --cov-report=html
open htmlcov/index.html

# Last failed tests only
pytest --lf

# Parallel execution (faster)
pytest -n auto
```

## Test Categories

### Integration Tests (tests/integration/)

| File | Tests | Purpose |
|------|-------|---------|
| `test_cache_aside.py` | 5 | Cache-Aside pattern validation |
| `test_crud_api.py` | 10 | REST API CRUD operations |
| `test_atomic_views.py` | 3 | Race condition prevention |
| `test_validation_api.py` | 7 | API input validation |
| `test_api_endpoints.py` | 4 | Health check, docs, root |

### Unit Tests (tests/unit/)

| File | Tests | Purpose |
|------|-------|---------|
| `test_schemas.py` | 8 | Pydantic schema validation |
| `test_post_service.py` | 5 | PostService business logic |

## Coverage Results

```
Unit tests only:     71% coverage (fast feedback)
Integration tests:   79% coverage (thorough validation)
All tests:           83% coverage (complete picture)
```

## Development Workflow

### 1. TDD Workflow (Red-Green-Refactor)
```bash
# Write failing test
pytest tests/unit/test_schemas.py::test_new_feature -v

# Implement feature
# ...

# Verify test passes
pytest tests/unit/test_schemas.py::test_new_feature -v

# Run all tests
pytest
```

### 2. Bug Fix Workflow
```bash
# Write failing test that reproduces bug
pytest tests/integration/test_bug_fix.py -v

# Fix bug
# ...

# Verify fix
pytest tests/integration/test_bug_fix.py -v

# Ensure no regressions
pytest
```

### 3. Feature Development Workflow
```bash
# Start with unit tests (fast)
pytest tests/unit/ -v

# Add integration tests
pytest tests/integration/ -v

# Full test suite
pytest --cov=src/blogcache
```

## CI/CD

Tests run automatically in GitHub Actions:
- ✅ 42 pytest tests
- ✅ 17 Newman/Postman API tests
- ✅ Coverage report generation
- ✅ ~15-20 seconds total

## Troubleshooting

### "Database not found"
```bash
docker-compose -f docker-compose.local.yml up postgres -d
```

### "Redis connection refused"
```bash
docker-compose -f docker-compose.local.yml up redis -d
```

### Flaky tests
```bash
# Run specific test multiple times
pytest tests/integration/test_atomic_views.py -v --count=10
```

### Clear test cache
```bash
rm -rf .pytest_cache __pycache__ .coverage htmlcov/
```

## Best Practices

✅ **DO:**
- Run unit tests frequently (fast feedback)
- Run integration tests before committing
- Write tests for bug fixes
- Keep tests isolated and independent
- Use descriptive test names

❌ **DON'T:**
- Skip tests to save time
- Write tests that depend on execution order
- Commit failing tests
- Test implementation details
- Mock everything (use real dependencies when possible)

## Performance Tips

```bash
# Parallel execution (4x faster)
pytest -n auto

# Profile slow tests
pytest --durations=10
```

## Documentation

For detailed documentation, see:
- `tests/README.md` - Comprehensive test documentation
- `TEST_REORGANIZATION.md` - Migration details
- `TEST_MANUAL.md` - Manual testing scenarios

## Quick Reference

```bash
# Development cycle
pytest tests/unit/ -v              # Fast feedback (2.5s)
pytest tests/integration/ -v       # Thorough check (12s)
pytest --cov=src/blogcache        # Full coverage (14s)

# Debugging
pytest tests/unit/test_schemas.py::test_post_create_valid -v -s

# Coverage
pytest --cov=src/blogcache --cov-report=term-missing
```
