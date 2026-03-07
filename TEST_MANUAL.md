# Manual Testing Guide 🧪

[English](#english) | [Русский](#russian)

---

<a name="english"></a>
## 🇬🇧 English

### Overview
This manual demonstrates **ACID compliance** and **race condition prevention** in the blogcache API through practical testing scenarios.

---

## 🔒 ACID Compliance Testing

### A - Atomicity
**Principle:** All operations complete fully or not at all.

#### Test 1: Post Creation with Database Rollback
```bash
# Start the application
docker-compose -f docker-compose.local.yml up

# Create a post
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Atomicity",
    "content": "Testing atomic operations",
    "author": "Tester"
  }'

# Expected: Post created with ID, or complete failure (no partial data)
```

**Verification:**
```bash
# Check database directly
docker exec -it blogcache-postgres-1 psql -U blogcache_user -d blogcache -c "SELECT * FROM posts;"

# Result: Either complete post exists or nothing (no orphaned data)
```

#### Test 2: Update with Validation Failure
```bash
# Try to update with invalid data (empty title)
curl -X PUT http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "",
    "content": "Updated content"
  }'

# Expected: 422 Validation Error, original data unchanged
```

**Verification:**
```bash
# Check that original data is intact
curl http://localhost:8000/posts/1

# Result: Original title and content remain unchanged
```

---

### C - Consistency
**Principle:** Database remains in valid state before and after transactions.

#### Test 3: Concurrent Updates Maintain Consistency
```bash
# Terminal 1: Update title
curl -X PUT http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title 1"}' &

# Terminal 2: Update content (immediately)
curl -X PUT http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated Content 2"}' &

# Wait for both to complete
wait

# Verify final state
curl http://localhost:8000/posts/1
```

**Expected Result:**
- Both updates applied (last write wins for each field)
- No data corruption
- All constraints satisfied (NOT NULL, length limits)

#### Test 4: Foreign Key Integrity (if applicable)
```bash
# Try to create post with invalid author reference
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "content": "Test",
    "author": ""
  }'

# Expected: 422 Validation Error (empty author not allowed)
```

---

### I - Isolation
**Principle:** Concurrent transactions don't interfere with each other.

#### Test 5: Read Isolation During Update
```bash
# Terminal 1: Start reading post repeatedly
for i in {1..10}; do
  curl http://localhost:8000/posts/1
  sleep 0.1
done &

# Terminal 2: Update post during reads
sleep 0.3
curl -X PUT http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated During Reads"}'
```

**Expected Result:**
- Reads return either old or new version (no partial data)
- No "dirty reads" (uncommitted data)
- No read errors during update

#### Test 6: Atomic View Counter (Race Condition Prevention)
```bash
# Create a post
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "View Counter Test",
    "content": "Testing atomic increments",
    "author": "Tester"
  }' | jq -r '.id')

# Simulate 10 concurrent requests from different IPs
for i in {1..10}; do
  curl -H "X-Forwarded-For: 192.168.1.$i" \
    http://localhost:8000/posts/$POST_ID &
done
wait

# Wait for background tasks to complete
sleep 1

# Check final view count
curl http://localhost:8000/posts/$POST_ID | jq '.views'

# Expected: views = 10 (exactly, no lost increments)
```

**Code Implementation (Atomic SQL):**
```python
# src/blogcache/services/post_service.py
await self.db.execute(
    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
    {"id": post_id},
)
```

**Why This Works:**
- Uses SQL-level atomic operation `views = views + 1`
- Database handles locking internally
- No race condition between read-modify-write

---

### D - Durability
**Principle:** Committed data survives system failures.

#### Test 7: Data Persistence After Restart
```bash
# Create a post
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Durability Test",
    "content": "This should survive restart",
    "author": "Tester"
  }'

# Note the post ID (e.g., 5)

# Restart containers
docker-compose -f docker-compose.local.yml restart

# Wait for startup
sleep 5

# Verify post still exists
curl http://localhost:8000/posts/5

# Expected: Post data intact after restart
```

#### Test 8: Cache vs Database Durability
```bash
# Create and cache a post
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cache Test",
    "content": "Testing cache durability",
    "author": "Tester"
  }' | jq -r '.id')

# Read to populate cache
curl http://localhost:8000/posts/$POST_ID

# Restart Redis only
docker-compose -f docker-compose.local.yml restart redis

# Wait for Redis startup
sleep 3

# Read again (cache miss, should fallback to DB)
curl http://localhost:8000/posts/$POST_ID

# Expected: Data retrieved successfully from PostgreSQL
```

---

## ⚡ Race Condition Prevention

### Problem: Lost Updates
**Scenario:** Two concurrent requests try to increment view counter.

#### ❌ Vulnerable Code (NOT USED):
```python
# BAD: Race condition possible
post = await db.get(post_id)
post.views += 1  # Read-Modify-Write race
await db.commit()
```

**Race Condition Timeline:**
```
Time | Request A          | Request B          | DB Value
-----|--------------------|--------------------|----------
t0   | Read views=10      |                    | 10
t1   |                    | Read views=10      | 10
t2   | Calculate 10+1=11  |                    | 10
t3   |                    | Calculate 10+1=11  | 10
t4   | Write views=11     |                    | 11
t5   |                    | Write views=11     | 11 ❌
```
**Result:** Lost update! Should be 12, but is 11.

---

### ✅ Solution: Atomic SQL Operations

#### Implementation:
```python
# GOOD: Atomic operation at database level
from sqlalchemy import text

await self.db.execute(
    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
    {"id": post_id},
)
await self.db.commit()
```

**Atomic Operation Timeline:**
```
Time | Request A          | Request B          | DB Value
-----|--------------------|--------------------|----------
t0   | UPDATE views+1     | (waiting for lock) | 10
t1   | Commit             | (waiting for lock) | 11 ✓
t2   |                    | UPDATE views+1     | 11
t3   |                    | Commit             | 12 ✓
```
**Result:** Correct! Both increments applied.

---

### Test 9: Concurrent View Increments
```bash
# Create test script
cat > test_race_condition.sh << 'EOF'
#!/bin/bash
POST_ID=$1
REQUESTS=50

echo "Testing $REQUESTS concurrent requests..."

# Launch concurrent requests
for i in $(seq 1 $REQUESTS); do
  curl -s -H "X-Forwarded-For: 10.0.0.$i" \
    http://localhost:8000/posts/$POST_ID > /dev/null &
done

# Wait for all requests
wait

# Wait for background tasks
sleep 2

# Check final count
VIEWS=$(curl -s http://localhost:8000/posts/$POST_ID | jq '.views')
echo "Expected: $REQUESTS"
echo "Actual: $VIEWS"

if [ "$VIEWS" -eq "$REQUESTS" ]; then
  echo "✅ PASS: No race condition detected"
else
  echo "❌ FAIL: Lost updates detected"
fi
EOF

chmod +x test_race_condition.sh

# Create a post
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Race Condition Test",
    "content": "Testing concurrent increments",
    "author": "Tester"
  }' | jq -r '.id')

# Run test
./test_race_condition.sh $POST_ID
```

**Expected Output:**
```
Testing 50 concurrent requests...
Expected: 50
Actual: 50
✅ PASS: No race condition detected
```

---

### Test 10: Unique View Tracking (IP-based Deduplication)
```bash
# Same IP multiple times should count as 1 view
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Unique View Test",
    "content": "Testing IP deduplication",
    "author": "Tester"
  }' | jq -r '.id')

# Make 5 requests from same IP
for i in {1..5}; do
  curl -H "X-Forwarded-For: 192.168.1.100" \
    http://localhost:8000/posts/$POST_ID
  sleep 0.2
done

# Check view count
VIEWS=$(curl -s http://localhost:8000/posts/$POST_ID | jq '.views')
echo "Views from same IP (5 requests): $VIEWS"

# Expected: views = 1 (deduplicated)
```

**Implementation:**
```python
# Redis-based unique tracking
view_key = f"view:{post_id}:{client_ip}"
exists = await redis.exists(view_key)

if not exists:
    await redis.setex(view_key, 86400, "1")  # 24h TTL
    return True  # Count this view
return False  # Skip duplicate
```

---

## 🔄 Cache Invalidation Testing

### Test 11: Cache Invalidation on Update
```bash
# Create and cache a post
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cache Invalidation Test",
    "content": "Original content",
    "author": "Tester"
  }' | jq -r '.id')

# Read to populate cache
curl http://localhost:8000/posts/$POST_ID

# Check Redis cache
docker exec -it blogcache-redis-1 redis-cli GET "post:$POST_ID"
# Should return cached JSON

# Update the post
curl -X PUT http://localhost:8000/posts/$POST_ID \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'

# Check Redis cache again
docker exec -it blogcache-redis-1 redis-cli GET "post:$POST_ID"
# Should return (nil) - cache invalidated

# Read again (cache miss, fresh from DB)
curl http://localhost:8000/posts/$POST_ID | jq '.title'
# Should return "Updated Title"
```

---

### Test 12: Cache Invalidation on Delete
```bash
# Create and cache a post
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Delete Test",
    "content": "Will be deleted",
    "author": "Tester"
  }' | jq -r '.id')

# Read to populate cache
curl http://localhost:8000/posts/$POST_ID

# Verify cache exists
docker exec -it blogcache-redis-1 redis-cli EXISTS "post:$POST_ID"
# Should return 1

# Delete the post
curl -X DELETE http://localhost:8000/posts/$POST_ID

# Verify cache removed
docker exec -it blogcache-redis-1 redis-cli EXISTS "post:$POST_ID"
# Should return 0

# Try to read (should return 404)
curl http://localhost:8000/posts/$POST_ID
# Expected: 404 Not Found
```

---

## 📊 Performance Testing

### Test 13: Cache Hit Performance
```bash
# Create a post
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Performance Test",
    "content": "Testing cache performance",
    "author": "Tester"
  }' | jq -r '.id')

# First request (cache miss - from DB)
time curl -s http://localhost:8000/posts/$POST_ID > /dev/null
# Note the time (e.g., 0.050s)

# Second request (cache hit - from Redis)
time curl -s http://localhost:8000/posts/$POST_ID > /dev/null
# Note the time (e.g., 0.010s)

# Cache hit should be significantly faster
```

---

## 🧪 Automated Test Suite

### Run All Tests
```bash
# Run pytest with coverage
docker-compose -f docker-compose.local.yml run --rm app \
  pytest --cov=src/blogcache --cov-report=html -v

# Key tests for ACID and race conditions:
# - test_concurrent_requests (race condition prevention)
# - test_unique_view_tracking (IP deduplication)
# - test_cache.py (cache invalidation)
# - test_service.py (CRUD operations)
```

### Specific Race Condition Test
```bash
# Run only concurrent test
docker-compose -f docker-compose.local.yml run --rm app \
  pytest tests/test_advanced.py::test_concurrent_requests -v

# Expected output:
# tests/test_advanced.py::test_concurrent_requests PASSED
```

---

## 🔍 Database Inspection

### Check View Counter Integrity
```bash
# Connect to PostgreSQL
docker exec -it blogcache-postgres-1 psql -U blogcache_user -d blogcache

# Check view counts
SELECT id, title, views FROM posts ORDER BY views DESC;

# Check for anomalies (negative views, NULL values)
SELECT COUNT(*) FROM posts WHERE views < 0 OR views IS NULL;
# Should return 0
```

### Check Redis Cache State
```bash
# Connect to Redis
docker exec -it blogcache-redis-1 redis-cli

# List all cached posts
KEYS post:*

# Check specific post cache
GET post:1

# Check TTL
TTL post:1
# Should return value between 0 and 300 (5 minutes)

# Check unique view tracking
KEYS view:*
```

---

<a name="russian"></a>
## 🇷🇺 Русский

### Обзор
Это руководство демонстрирует **соответствие ACID** и **предотвращение race condition** в API blogcache через практические сценарии тестирования.

---

## 🔒 Тестирование соответствия ACID

### A - Атомарность
**Принцип:** Все операции выполняются полностью или не выполняются вообще.

#### Тест 1: Создание поста с откатом БД
```bash
# Запустить приложение
docker-compose -f docker-compose.local.yml up

# Создать пост
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тест атомарности",
    "content": "Тестирование атомарных операций",
    "author": "Тестер"
  }'

# Ожидается: Пост создан с ID, или полный отказ (нет частичных данных)
```

**Проверка:**
```bash
# Проверить БД напрямую
docker exec -it blogcache-postgres-1 psql -U blogcache_user -d blogcache -c "SELECT * FROM posts;"

# Результат: Либо полный пост существует, либо ничего (нет потерянных данных)
```

---

### C - Согласованность
**Принцип:** БД остается в валидном состоянии до и после транзакций.

#### Тест 3: Конкурентные обновления сохраняют согласованность
```bash
# Терминал 1: Обновить заголовок
curl -X PUT http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Обновленный заголовок 1"}' &

# Терминал 2: Обновить контент (немедленно)
curl -X PUT http://localhost:8000/posts/1 \
  -H "Content-Type: application/json" \
  -d '{"content": "Обновленный контент 2"}' &

# Дождаться завершения обоих
wait

# Проверить финальное состояние
curl http://localhost:8000/posts/1
```

**Ожидаемый результат:**
- Оба обновления применены (последняя запись побеждает для каждого поля)
- Нет повреждения данных
- Все ограничения соблюдены (NOT NULL, лимиты длины)

---

### I - Изоляция
**Принцип:** Конкурентные транзакции не мешают друг другу.

#### Тест 6: Атомарный счетчик просмотров (предотвращение race condition)
```bash
# Создать пост
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тест счетчика просмотров",
    "content": "Тестирование атомарных инкрементов",
    "author": "Тестер"
  }' | jq -r '.id')

# Симулировать 10 конкурентных запросов с разных IP
for i in {1..10}; do
  curl -H "X-Forwarded-For: 192.168.1.$i" \
    http://localhost:8000/posts/$POST_ID &
done
wait

# Дождаться завершения фоновых задач
sleep 1

# Проверить финальный счетчик просмотров
curl http://localhost:8000/posts/$POST_ID | jq '.views'

# Ожидается: views = 10 (точно, нет потерянных инкрементов)
```

**Реализация в коде (атомарный SQL):**
```python
# src/blogcache/services/post_service.py
await self.db.execute(
    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
    {"id": post_id},
)
```

**Почему это работает:**
- Использует атомарную операцию на уровне SQL `views = views + 1`
- БД обрабатывает блокировки внутренне
- Нет race condition между read-modify-write

---

### D - Долговечность
**Принцип:** Зафиксированные данные переживают сбои системы.

#### Тест 7: Сохранность данных после перезапуска
```bash
# Создать пост
curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тест долговечности",
    "content": "Это должно пережить перезапуск",
    "author": "Тестер"
  }'

# Запомнить ID поста (например, 5)

# Перезапустить контейнеры
docker-compose -f docker-compose.local.yml restart

# Дождаться запуска
sleep 5

# Проверить, что пост все еще существует
curl http://localhost:8000/posts/5

# Ожидается: Данные поста целы после перезапуска
```

---

## ⚡ Предотвращение Race Condition

### Проблема: Потерянные обновления
**Сценарий:** Два конкурентных запроса пытаются инкрементировать счетчик просмотров.

#### ❌ Уязвимый код (НЕ ИСПОЛЬЗУЕТСЯ):
```python
# ПЛОХО: Возможна race condition
post = await db.get(post_id)
post.views += 1  # Race condition при Read-Modify-Write
await db.commit()
```

**Временная шкала race condition:**
```
Время | Запрос A           | Запрос B           | Значение БД
------|--------------------|--------------------|-------------
t0    | Читает views=10    |                    | 10
t1    |                    | Читает views=10    | 10
t2    | Вычисляет 10+1=11  |                    | 10
t3    |                    | Вычисляет 10+1=11  | 10
t4    | Пишет views=11     |                    | 11
t5    |                    | Пишет views=11     | 11 ❌
```
**Результат:** Потерянное обновление! Должно быть 12, но получилось 11.

---

### ✅ Решение: Атомарные SQL операции

#### Реализация:
```python
# ХОРОШО: Атомарная операция на уровне БД
from sqlalchemy import text

await self.db.execute(
    text("UPDATE posts SET views = views + 1 WHERE id = :id"),
    {"id": post_id},
)
await self.db.commit()
```

**Временная шкала атомарной операции:**
```
Время | Запрос A           | Запрос B           | Значение БД
------|--------------------|--------------------|-------------
t0    | UPDATE views+1     | (ждет блокировки)  | 10
t1    | Commit             | (ждет блокировки)  | 11 ✓
t2    |                    | UPDATE views+1     | 11
t3    |                    | Commit             | 12 ✓
```
**Результат:** Правильно! Оба инкремента применены.

---

### Тест 9: Конкурентные инкременты просмотров
```bash
# Создать тестовый скрипт
cat > test_race_condition.sh << 'EOF'
#!/bin/bash
POST_ID=$1
REQUESTS=50

echo "Тестирование $REQUESTS конкурентных запросов..."

# Запустить конкурентные запросы
for i in $(seq 1 $REQUESTS); do
  curl -s -H "X-Forwarded-For: 10.0.0.$i" \
    http://localhost:8000/posts/$POST_ID > /dev/null &
done

# Дождаться всех запросов
wait

# Дождаться фоновых задач
sleep 2

# Проверить финальный счетчик
VIEWS=$(curl -s http://localhost:8000/posts/$POST_ID | jq '.views')
echo "Ожидается: $REQUESTS"
echo "Фактически: $VIEWS"

if [ "$VIEWS" -eq "$REQUESTS" ]; then
  echo "✅ УСПЕХ: Race condition не обнаружена"
else
  echo "❌ ПРОВАЛ: Обнаружены потерянные обновления"
fi
EOF

chmod +x test_race_condition.sh

# Создать пост
POST_ID=$(curl -X POST http://localhost:8000/posts/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Тест Race Condition",
    "content": "Тестирование конкурентных инкрементов",
    "author": "Тестер"
  }' | jq -r '.id')

# Запустить тест
./test_race_condition.sh $POST_ID
```

**Ожидаемый вывод:**
```
Тестирование 50 конкурентных запросов...
Ожидается: 50
Фактически: 50
✅ УСПЕХ: Race condition не обнаружена
```

---

## 🧪 Автоматизированный набор тестов

### Запустить все тесты
```bash
# Запустить pytest с покрытием
docker-compose -f docker-compose.local.yml run --rm app \
  pytest --cov=src/blogcache --cov-report=html -v

# Ключевые тесты для ACID и race conditions:
# - test_concurrent_requests (предотвращение race condition)
# - test_unique_view_tracking (дедупликация по IP)
# - test_cache.py (инвалидация кеша)
# - test_service.py (CRUD операции)
```

---

## 📄 License
MIT

## 👤 Author
Dmitrij Valedinskij
