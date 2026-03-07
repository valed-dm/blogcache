# blogcache 📝⚡

[English](#english) | [Русский](#russian)

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-86%25_coverage-0A9EDC?style=flat&logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

<a name="english"></a>
## 🇬🇧 English

### Overview
High-performance blog API built with **FastAPI** and **Redis caching** to optimize read operations for popular posts. Implements the **Cache-Aside** pattern with automatic cache invalidation.

### ✨ Features
- ✍️ **Full CRUD operations** for blog posts (Create, Read, Update, Delete)
- 🚀 **Redis caching** with Cache-Aside pattern
- 🔄 **Automatic cache invalidation** on updates/deletes
- 👁️ **Unique view tracking** (one view per IP per 24 hours)
- ⚡ **Atomic view counter** (race condition safe)
- 🗄️ **Async SQLAlchemy** + PostgreSQL with asyncpg
- 🔧 **Alembic migrations** for database version control
- 🐳 **Docker Compose** setup (PostgreSQL + Redis)
- 🧪 **Integration tests** with 86% coverage (25 tests)
- 📚 **Auto-generated OpenAPI docs** at `/docs`

### 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────┐
│         FastAPI Router              │
│    (src/blogcache/api/posts.py)     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│       PostService Layer             │
│ (src/blogcache/services/post_service.py) │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Cache-Aside Pattern:       │  │
│  │   1. Check Redis             │  │
│  │   2. If miss → PostgreSQL    │  │
│  │   3. Store in Redis (5min)   │  │
│  │   4. Return data             │  │
│  └──────────────────────────────┘  │
└──────┬────────────────────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│    Redis    │      │ PostgreSQL  │
│   (Cache)   │      │  (Database) │
└─────────────┘      └─────────────┘
```

### 🎯 Why Cache-Aside Pattern?

**Chosen approach:** Cache-Aside (Lazy Loading)

**Reasons:**
1. **Efficiency** — Only popular posts are cached, no wasted memory
2. **Simplicity** — Application controls cache logic explicitly
3. **Resilience** — Cache failures don't break the application (fallback to DB)
4. **Consistency** — Easy to invalidate cache on updates/deletes
5. **Standard pattern** — Well-documented, battle-tested approach

**How it works:**
- **Read:** Check Redis → Miss? → Query PostgreSQL → Store in Redis (TTL: 5 min) → Return
- **Write/Update/Delete:** Update PostgreSQL → Invalidate Redis cache → Return

**Alternative considered:** Write-Through (rejected due to complexity and unnecessary writes for unpopular posts)

### 🛠️ Tech Stack
- **Framework:** FastAPI 0.115+
- **Database:** PostgreSQL 17 (asyncpg driver)
- **ORM:** SQLAlchemy 2.0 + Alembic
- **Cache:** Redis 7
- **Testing:** pytest + pytest-asyncio
- **Containerization:** Docker + Docker Compose

### 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/posts/` | Create new post |
| `GET` | `/posts/{id}` | Get post by ID (cached) |
| `PUT` | `/posts/{id}` | Update post (invalidates cache) |
| `DELETE` | `/posts/{id}` | Delete post (invalidates cache) |
| `GET` | `/docs` | OpenAPI documentation |

### 🚀 Installation & Setup

#### Prerequisites
- Docker & Docker Compose
- Python 3.12+ (for local development)
- Poetry (for dependency management)

#### 1. Clone Repository
```bash
git clone <repository-url>
cd blogcache
```

#### 2. Environment Configuration
```bash
# Copy example environment file
cp docker.env.example docker.env

# Edit docker.env with your settings (optional, defaults work)
```

**Key environment variables:**
```env
POSTGRES_USER=blogcache_user
POSTGRES_PASSWORD=blogcache_pass
POSTGRES_DB=blogcache
REDIS_HOST=redis
REDIS_PORT=6379
```

#### 3. Run with Docker Compose

**Development mode (with hot reload):**
```bash
docker-compose -f docker-compose.local.yml up --build
```

**Production mode:**
```bash
docker-compose -f docker-compose.prod.yml up --build
```

Application will be available at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

#### 4. Local Development (without Docker)

```bash
# Install dependencies
poetry install

# Start PostgreSQL and Redis
docker-compose -f docker-compose.local.yml up postgres redis

# Run migrations
poetry run alembic upgrade head

# Start application
poetry run uvicorn blogcache.main:app --reload
```

### 🧪 Running Tests

#### With Docker:
```bash
# Run all tests with coverage
docker-compose -f docker-compose.local.yml run --rm app pytest --cov=src/blogcache --cov-report=html

# Run specific test file
docker-compose -f docker-compose.local.yml run --rm app pytest tests/test_cache.py -v
```

#### Locally:
```bash
# Ensure PostgreSQL and Redis are running
docker-compose -f docker-compose.local.yml up postgres redis -d

# Run tests
poetry run pytest --cov=src/blogcache --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test coverage:** 86% (25 tests passing)

**Test categories:**
- `test_cache.py` — Cache-Aside pattern integration tests
- `test_service.py` — PostService business logic tests
- `test_advanced.py` — Concurrent requests & unique view tracking
- `test_validation.py` — Input validation tests

### 🗄️ Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

Migrations run automatically on container startup via `docker-entrypoint.sh`.

### 📊 Database Schema

**Table: `posts`**
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(100) NOT NULL,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

**Indexes:**
- `PRIMARY KEY (id)` — Fast lookups by ID
- `idx_posts_created_at` — Optimized for sorting by date

### 🔒 Error Handling
- **404 Not Found** — Post doesn't exist
- **422 Unprocessable Entity** — Validation errors
- **500 Internal Server Error** — Database/Redis failures (logged)

### 📁 Project Structure
```
blogcache/
├── src/blogcache/
│   ├── api/              # FastAPI routers
│   ├── core/             # Config, database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic (PostService)
│   └── main.py           # Application entry point
├── tests/                # Integration & unit tests
├── alembic/              # Database migrations
├── scripts/              # Docker entrypoint scripts
├── docker-compose.*.yml  # Docker configurations
├── Dockerfile            # Development image
├── Dockerfile.prod       # Production image
└── pyproject.toml        # Poetry dependencies
```

### 🎓 Code Quality
- **Clean architecture** — Separation of concerns (API → Service → Repository)
- **Type hints** — Full typing with mypy support
- **Async/await** — Non-blocking I/O operations
- **Dependency injection** — FastAPI's DI system
- **Error handling** — Proper HTTP status codes
- **Testing** — Integration tests for cache logic

---

<a name="russian"></a>
## 🇷🇺 Русский

### Обзор
Высокопроизводительный API для блога на **FastAPI** с **кешированием в Redis** для оптимизации чтения популярных постов. Реализует паттерн **Cache-Aside** с автоматической инвалидацией кеша.

### ✨ Возможности
- ✍️ **Полный CRUD** для постов блога (создание, чтение, обновление, удаление)
- 🚀 **Кеширование в Redis** по паттерну Cache-Aside
- 🔄 **Автоматическая инвалидация кеша** при обновлении/удалении
- 👁️ **Учет уникальных просмотров** (один просмотр с IP за 24 часа)
- ⚡ **Атомарный счетчик просмотров** (защита от race condition)
- 🗄️ **Async SQLAlchemy** + PostgreSQL с asyncpg
- 🔧 **Миграции Alembic** для версионирования БД
- 🐳 **Docker Compose** (PostgreSQL + Redis)
- 🧪 **Интеграционные тесты** с покрытием 86% (25 тестов)
- 📚 **Автогенерация OpenAPI документации** на `/docs`

### 🏗️ Архитектура

```
┌─────────────┐
│   Клиент    │
└──────┬──────┘
       │ HTTP запрос
       ▼
┌─────────────────────────────────────┐
│       FastAPI Router                │
│    (src/blogcache/api/posts.py)     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│       Слой PostService              │
│ (src/blogcache/services/post_service.py) │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Паттерн Cache-Aside:       │  │
│  │   1. Проверка Redis          │  │
│  │   2. Промах → PostgreSQL     │  │
│  │   3. Сохранение в Redis (5м) │  │
│  │   4. Возврат данных          │  │
│  └──────────────────────────────┘  │
└──────┬────────────────────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│    Redis    │      │ PostgreSQL  │
│    (Кеш)    │      │    (БД)     │
└─────────────┘      └─────────────┘
```

### 🎯 Почему паттерн Cache-Aside?

**Выбранный подход:** Cache-Aside (Ленивая загрузка)

**Причины выбора:**
1. **Эффективность** — Кешируются только популярные посты, нет лишних данных в памяти
2. **Простота** — Приложение явно контролирует логику кеширования
3. **Устойчивость** — Сбои кеша не ломают приложение (fallback на БД)
4. **Консистентность** — Легко инвалидировать кеш при изменениях
5. **Стандартный паттерн** — Хорошо документирован, проверен в production

**Как работает:**
- **Чтение:** Проверка Redis → Промах? → Запрос PostgreSQL → Сохранение в Redis (TTL: 5 мин) → Возврат
- **Запись/Обновление/Удаление:** Обновление PostgreSQL → Инвалидация кеша Redis → Возврат

**Альтернатива:** Write-Through (отклонена из-за сложности и лишних записей для непопулярных постов)

### 🛠️ Технологический стек
- **Фреймворк:** FastAPI 0.115+
- **База данных:** PostgreSQL 17 (драйвер asyncpg)
- **ORM:** SQLAlchemy 2.0 + Alembic
- **Кеш:** Redis 7
- **Тестирование:** pytest + pytest-asyncio
- **Контейнеризация:** Docker + Docker Compose

### 📋 API endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/posts/` | Создать новый пост |
| `GET` | `/posts/{id}` | Получить пост по ID (с кешированием) |
| `PUT` | `/posts/{id}` | Обновить пост (инвалидирует кеш) |
| `DELETE` | `/posts/{id}` | Удалить пост (инвалидирует кеш) |
| `GET` | `/docs` | OpenAPI документация |

### 🚀 Установка и запуск

#### Требования
- Docker & Docker Compose
- Python 3.12+ (для локальной разработки)
- Poetry (для управления зависимостями)

#### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd blogcache
```

#### 2. Настройка окружения
```bash
# Копируем пример файла окружения
cp docker.env.example docker.env

# Редактируем docker.env при необходимости (дефолтные значения работают)
```

**Основные переменные окружения:**
```env
POSTGRES_USER=blogcache_user
POSTGRES_PASSWORD=blogcache_pass
POSTGRES_DB=blogcache
REDIS_HOST=redis
REDIS_PORT=6379
```

#### 3. Запуск через Docker Compose

**Режим разработки (с hot reload):**
```bash
docker-compose -f docker-compose.local.yml up --build
```

**Production режим:**
```bash
docker-compose -f docker-compose.prod.yml up --build
```

Приложение доступно по адресу: **http://localhost:8000**

API документация: **http://localhost:8000/docs**

#### 4. Локальная разработка (без Docker)

```bash
# Установка зависимостей
poetry install

# Запуск PostgreSQL и Redis
docker-compose -f docker-compose.local.yml up postgres redis

# Применение миграций
poetry run alembic upgrade head

# Запуск приложения
poetry run uvicorn blogcache.main:app --reload
```

### 🧪 Запуск тестов

#### С Docker:
```bash
# Запуск всех тестов с покрытием
docker-compose -f docker-compose.local.yml run --rm app pytest --cov=src/blogcache --cov-report=html

# Запуск конкретного файла тестов
docker-compose -f docker-compose.local.yml run --rm app pytest tests/test_cache.py -v
```

#### Локально:
```bash
# Убедитесь, что PostgreSQL и Redis запущены
docker-compose -f docker-compose.local.yml up postgres redis -d

# Запуск тестов
poetry run pytest --cov=src/blogcache --cov-report=html

# Просмотр отчета о покрытии
open htmlcov/index.html
```

**Покрытие тестами:** 86% (25 тестов проходят)

**Категории тестов:**
- `test_cache.py` — Интеграционные тесты паттерна Cache-Aside
- `test_service.py` — Тесты бизнес-логики PostService
- `test_advanced.py` — Конкурентные запросы и уникальные просмотры
- `test_validation.py` — Тесты валидации входных данных

### 🗄️ Миграции базы данных

```bash
# Создание новой миграции
poetry run alembic revision --autogenerate -m "описание"

# Применение миграций
poetry run alembic upgrade head

# Откат миграции
poetry run alembic downgrade -1
```

Миграции применяются автоматически при старте контейнера через `docker-entrypoint.sh`.

### 📊 Схема базы данных

**Таблица: `posts`**
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(100) NOT NULL,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

**Индексы:**
- `PRIMARY KEY (id)` — Быстрый поиск по ID
- `idx_posts_created_at` — Оптимизация сортировки по дате

### 🔒 Обработка ошибок
- **404 Not Found** — Пост не существует
- **422 Unprocessable Entity** — Ошибки валидации
- **500 Internal Server Error** — Сбои БД/Redis (логируются)

### 📁 Структура проекта
```
blogcache/
├── src/blogcache/
│   ├── api/              # FastAPI роутеры
│   ├── core/             # Конфигурация, настройка БД
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика (PostService)
│   └── main.py           # Точка входа приложения
├── tests/                # Интеграционные и unit тесты
├── alembic/              # Миграции БД
├── scripts/              # Скрипты для Docker
├── docker-compose.*.yml  # Конфигурации Docker
├── Dockerfile            # Development образ
├── Dockerfile.prod       # Production образ
└── pyproject.toml        # Зависимости Poetry
```

### 🎓 Качество кода
- **Чистая архитектура** — Разделение ответственности (API → Service → Repository)
- **Аннотации типов** — Полная типизация с поддержкой mypy
- **Async/await** — Неблокирующие I/O операции
- **Dependency injection** — Система DI FastAPI
- **Обработка ошибок** — Корректные HTTP статус-коды
- **Тестирование** — Интеграционные тесты логики кеширования

---

## 📄 License
MIT

## 👤 Author
Dmitrij Valedinskij

## 🔗 Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Cache-Aside Pattern](https://redis.io/docs/manual/patterns/cache-aside/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
