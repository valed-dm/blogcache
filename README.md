# blogcache 📝⚡

A high-performance blog API built with **FastAPI** and **Redis caching** to optimize read operations for popular posts.

## Features
- ✍️ Full CRUD operations for blog posts
- 🚀 Redis caching with Cache-Aside pattern
- 🔄 Automatic cache invalidation on updates/deletes
- 🗄️ Async SQLAlchemy + PostgreSQL
- 📦 Docker Compose setup (PostgreSQL + Redis)
- 🧪 Integration tests for cache logic
- 📚 Auto-generated OpenAPI docs at `/docs`

## Tech Stack
- **Framework:** FastAPI
- **Database:** PostgreSQL (asyncpg)
- **ORM:** SQLAlchemy 2.0 + Alembic
- **Cache:** Redis
- **Testing:** pytest

## Why caching?
Reduces database load for popular posts by serving frequently accessed content directly from Redis. Implements the standard **Cache-Aside** pattern:
1. Check Redis → if miss → query PostgreSQL → store in Redis → return
2. Cache invalidation on write operations
