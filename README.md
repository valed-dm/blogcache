# blogcache 📝⚡

[English](#english) | [Русский](#russian)

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-83%25_coverage-0A9EDC?style=flat&logo=pytest&logoColor=white)
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
- 🏗️ **Clean Architecture** (Repository Pattern + DTOs)
- 📊 **Prometheus metrics** for monitoring
- 🛡️ **Rate limiting** (100/min global, 10/min for POST)
- 🏥 **Health checks** with dependency status
- 📝 **Structured logging** with Loguru (rotation + compression)
- 🔧 **Alembic migrations** for database version control
- 🐳 **Docker Compose** setup (PostgreSQL + Redis)
- 🧪 **53 tests** with 83% coverage (29 integration + 24 unit tests)
- 📚 **Auto-generated OpenAPI docs** at `/docs`

### 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────┐
│      FastAPI Router + Middleware    │
│  (Rate Limiter, Exception Handlers) │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│       PostService (Business Logic)  │
│         Uses DTOs internally        │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Cache-Aside Pattern:       │  │
│  │   1. Check CacheService      │  │
│  │   2. If miss → Repository    │  │
│  │   3. Store in Cache (5min)   │  │
│  │   4. Return DTO              │  │
│  └──────────────────────────────┘  │
└──────┬────────────────────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│CacheService │      │PostRepository│
│   (Redis)   │      │ (Data Access)│
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ PostgreSQL  │
                     │  (Database) │
                     └─────────────┘
```

**Key Architecture Patterns:**
- **Repository Pattern** — Data access abstraction (PostRepository)
- **Service Layer** — Business logic (PostService)
- **DTOs** — Internal data transfer (PostDTO)
- **Dependency Injection** — FastAPI's DI system
- **Exception Handling** — Custom exceptions with handlers
- **Observability** — Prometheus metrics + structured logging

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

**Alternative considered:** Write-Through (rejected)

**Why Write-Through was rejected:**
- **Wasted resources** — Every post write goes to both DB and cache, even if post is never read
- **Cache pollution** — Unpopular posts consume cache memory unnecessarily
- **Complexity** — Requires synchronous writes to two systems, increasing latency
- **Failure handling** — If cache write fails, need rollback logic or accept inconsistency
- **No clear benefit** — Most posts are read rarely, so pre-caching doesn't help

**When Write-Through would be better:**
- High read-to-write ratio for ALL posts (not just popular ones)
- Strict requirement that first read must be fast (no cache miss allowed)
- Cache is primary data store with DB as backup

### 🛠️ Tech Stack
- **Framework:** FastAPI 0.115+
- **Database:** PostgreSQL 17 (asyncpg driver)
- **ORM:** SQLAlchemy 2.0 + Alembic
- **Cache:** Redis 7
- **Testing:** pytest + pytest-asyncio
- **Containerization:** Docker + Docker Compose

### 📋 API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/posts/` | Create new post | 10/min |
| `GET` | `/posts/{id}` | Get post by ID (cached) | 100/min |
| `PUT` | `/posts/{id}` | Update post (invalidates cache) | 100/min |
| `DELETE` | `/posts/{id}` | Delete post (invalidates cache) | 100/min |
| `GET` | `/health` | Health check with dependency status | - |
| `GET` | `/metrics` | Prometheus metrics | - |
| `GET` | `/docs` | OpenAPI documentation | - |

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

**Test coverage:** 83% (53 tests passing)

**Test structure:**
- `integration/` — 29 tests for Cache-Aside, CRUD API, atomic views, validation
- `unit/` — 24 tests for schemas, DTOs, services, config, health checks, metrics
- See `tests/README.md` for detailed documentation

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
- **404 Not Found** — Post doesn't exist (PostNotFoundError)
- **422 Unprocessable Entity** — Validation errors
- **429 Too Many Requests** — Rate limit exceeded
- **500 Internal Server Error** — Database/Redis failures (DatabaseError, CacheError)
- **503 Service Unavailable** — Health check failed

**Custom Exceptions:**
- `BlogCacheException` — Base exception
- `PostNotFoundError` — Post not found
- `CacheError` — Redis operation failed
- `DatabaseError` — PostgreSQL operation failed

### 📁 Project Structure
```
blogcache/
├── src/blogcache/
│   ├── api/              # FastAPI routers
│   ├── core/             # Config, database, exceptions, logging, metrics
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas (API layer)
│   ├── dto/              # Data Transfer Objects (internal)
│   ├── services/         # Business logic (PostService, CacheService)
│   ├── repositories/     # Data access layer (PostRepository)
│   └── main.py           # Application entry point
├── tests/
│   ├── integration/      # 29 integration tests (API, cache, DB)
│   ├── unit/             # 24 unit tests (schemas, DTOs, services)
│   └── README.md         # Test documentation
├── alembic/              # Database migrations
├── scripts/              # Docker entrypoint scripts
├── docker-compose.*.yml  # Docker configurations
├── Dockerfile            # Development image
├── Dockerfile.prod       # Production image
└── pyproject.toml        # Poetry dependencies
```

### 🎓 Code Quality
- **Clean Architecture** — Layered design (API → Service → Repository → Database)
- **Repository Pattern** — Data access abstraction
- **DTOs** — Decoupled internal data transfer
- **Type hints** — Full typing with mypy compliance
- **Async/await** — Non-blocking I/O operations
- **Dependency Injection** — FastAPI's DI system
- **Custom Exceptions** — Proper error handling with context
- **Structured Logging** — Loguru with rotation (10MB, 7 days, zip)
- **Observability** — Prometheus metrics (cache hits, DB queries, request duration)
- **Rate Limiting** — Protection against abuse (slowapi)
- **Testing** — 53 tests (29 integration + 24 unit) with 83% coverage

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
- 🏗️ **Чистая архитектура** (Repository Pattern + DTO)
- 📊 **Метрики Prometheus** для мониторинга
- 🛡️ **Rate limiting** (100/мин глобально, 10/мин для POST)
- 🏥 **Health checks** со статусом зависимостей
- 📝 **Структурированное логирование** с Loguru (ротация + сжатие)
- 🔧 **Миграции Alembic** для версионирования БД
- 🐳 **Docker Compose** (PostgreSQL + Redis)
- 🧪 **53 теста** с покрытием 83% (29 интеграционных + 24 unit тестов)
- 📚 **Автогенерация OpenAPI документации** на `/docs`

### 🏗️ Архитектура

```
┌─────────────┐
│   Клиент    │
└──────┬──────┘
       │ HTTP запрос
       ▼
┌─────────────────────────────────────┐
│   FastAPI Router + Middleware       │
│  (Rate Limiter, Exception Handlers) │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   PostService (Бизнес-логика)       │
│      Использует DTO внутри          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Паттерн Cache-Aside:       │  │
│  │   1. Проверка CacheService   │  │
│  │   2. Промах → Repository     │  │
│  │   3. Сохранение в Cache (5м) │  │
│  │   4. Возврат DTO             │  │
│  └──────────────────────────────┘  │
└──────┬────────────────────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│CacheService │      │PostRepository│
│   (Redis)   │      │(Доступ к БД)│
└─────────────┘      └──────┬───────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ PostgreSQL  │
                     │    (БД)     │
                     └─────────────┘
```

**Ключевые архитектурные паттерны:**
- **Repository Pattern** — Абстракция доступа к данным (PostRepository)
- **Service Layer** — Бизнес-логика (PostService)
- **DTO** — Внутренняя передача данных (PostDTO)
- **Dependency Injection** — Система DI FastAPI
- **Exception Handling** — Кастомные исключения с обработчиками
- **Observability** — Метрики Prometheus + структурированное логирование

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

**Альтернатива:** Write-Through (отклонена)

**Почему Write-Through был отклонен:**
- **Расход ресурсов** — Каждая запись идет и в БД, и в кеш, даже если пост никогда не прочитают
- **Засорение кеша** — Непопулярные посты занимают память кеша без пользы
- **Сложность** — Требует синхронной записи в две системы, увеличивая задержку
- **Обработка ошибок** — При сбое записи в кеш нужна логика отката или принятие несогласованности
- **Нет явной выгоды** — Большинство постов читаются редко, поэтому предварительное кеширование не помогает

**Когда Write-Through был бы лучше:**
- Высокое соотношение чтения к записи для ВСЕХ постов (не только популярных)
- Строгое требование, чтобы первое чтение было быстрым (промах кеша недопустим)
- Кеш является основным хранилищем данных с БД в качестве резервной копии

### 🛠️ Технологический стек
- **Фреймворк:** FastAPI 0.115+
- **База данных:** PostgreSQL 17 (драйвер asyncpg)
- **ORM:** SQLAlchemy 2.0 + Alembic
- **Кеш:** Redis 7
- **Тестирование:** pytest + pytest-asyncio
- **Контейнеризация:** Docker + Docker Compose

### 📋 API endpoints

| Метод | Endpoint | Описание | Rate Limit |
|-------|----------|----------|------------|
| `POST` | `/posts/` | Создать новый пост | 10/мин |
| `GET` | `/posts/{id}` | Получить пост по ID (с кешированием) | 100/мин |
| `PUT` | `/posts/{id}` | Обновить пост (инвалидирует кеш) | 100/мин |
| `DELETE` | `/posts/{id}` | Удалить пост (инвалидирует кеш) | 100/мин |
| `GET` | `/health` | Health check со статусом зависимостей | - |
| `GET` | `/metrics` | Метрики Prometheus | - |
| `GET` | `/docs` | OpenAPI документация | - |

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

**Покрытие тестами:** 83% (53 теста проходят)

**Структура тестов:**
- `integration/` — 29 тестов для Cache-Aside, CRUD API, атомарных просмотров, валидации
- `unit/` — 24 теста для схем, DTO, сервисов, конфигурации, health checks, метрик
- См. `tests/README.md` для подробной документации

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
- **404 Not Found** — Пост не существует (PostNotFoundError)
- **422 Unprocessable Entity** — Ошибки валидации
- **429 Too Many Requests** — Превышен rate limit
- **500 Internal Server Error** — Сбои БД/Redis (DatabaseError, CacheError)
- **503 Service Unavailable** — Health check провален

**Кастомные исключения:**
- `BlogCacheException` — Базовое исключение
- `PostNotFoundError` — Пост не найден
- `CacheError` — Ошибка операции Redis
- `DatabaseError` — Ошибка операции PostgreSQL

### 📁 Структура проекта
```
blogcache/
├── src/blogcache/
│   ├── api/              # FastAPI роутеры
│   ├── core/             # Конфигурация, БД, исключения, логирование, метрики
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы (API слой)
│   ├── dto/              # Data Transfer Objects (внутренние)
│   ├── services/         # Бизнес-логика (PostService, CacheService)
│   ├── repositories/     # Слой доступа к данным (PostRepository)
│   └── main.py           # Точка входа приложения
├── tests/
│   ├── integration/      # 29 интеграционных тестов (API, кеш, БД)
│   ├── unit/             # 24 unit теста (схемы, DTO, сервисы)
│   └── README.md         # Документация тестов
├── alembic/              # Миграции БД
├── scripts/              # Скрипты для Docker
├── docker-compose.*.yml  # Конфигурации Docker
├── Dockerfile            # Development образ
├── Dockerfile.prod       # Production образ
└── pyproject.toml        # Зависимости Poetry
```

### 🎓 Качество кода
- **Чистая архитектура** — Слоистый дизайн (API → Service → Repository → Database)
- **Repository Pattern** — Абстракция доступа к данным
- **DTO** — Разделенная внутренняя передача данных
- **Аннотации типов** — Полная типизация с соответствием mypy
- **Async/await** — Неблокирующие I/O операции
- **Dependency Injection** — Система DI FastAPI
- **Кастомные исключения** — Правильная обработка ошибок с контекстом
- **Структурированное логирование** — Loguru с ротацией (10MB, 7 дней, zip)
- **Observability** — Метрики Prometheus (попадания в кеш, запросы к БД, длительность запросов)
- **Rate Limiting** — Защита от злоупотреблений (slowapi)
- **Тестирование** — 53 теста (29 интеграционных + 24 unit) с покрытием 83%

---

## 📄 License
MIT

## 👤 Author
Dmitrij Valedinskij

## 🔗 Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Cache-Aside Pattern](https://redis.io/tutorials/howtos/solutions/microservices/caching/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
