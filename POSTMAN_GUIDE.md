# Postman Collection for BlogCache API 📮

## Overview
Complete Postman collection for automated testing of all BlogCache API endpoints with built-in test assertions.

## Files
- `postman_collection.json` - Main collection with 17 test requests
- `postman_environment.json` - Environment variables configuration

## Features
✅ **17 Test Requests** covering:
- Health check
- CRUD operations (Create, Read, Update, Delete)
- Cache hit/miss scenarios
- Unique view tracking with different IPs
- Pagination testing
- Validation error handling
- 404 error scenarios

✅ **Automated Test Assertions**:
- Status code validation
- Response structure verification
- Data integrity checks
- Performance benchmarks
- Cache invalidation verification

✅ **Dynamic Variables**:
- `{{base_url}}` - API base URL (default: http://localhost:8000)
- `{{post_id}}` - Auto-captured from create response

## Installation

### Method 1: Import via Postman UI
1. Open Postman
2. Click **Import** button
3. Select `postman_collection.json`
4. Select `postman_environment.json`
5. Select "BlogCache Local Environment" from environment dropdown

### Method 2: Import via URL (if hosted on GitHub)
1. Open Postman
2. Click **Import** → **Link**
3. Paste raw GitHub URL to `postman_collection.json`
4. Repeat for `postman_environment.json`

## Usage

### Prerequisites
```bash
# Start the application
docker-compose -f docker-compose.local.yml up
```

### Running Tests

#### 1. Run Entire Collection
1. Click on "BlogCache API - Complete Test Suite" collection
2. Click **Run** button
3. Select all requests
4. Click **Run BlogCache API**
5. View test results

**Expected Result:** All 17 tests pass ✅

#### 2. Run Individual Request
1. Select any request from the collection
2. Click **Send**
3. View response and test results in **Test Results** tab

#### 3. Run via Newman (CLI)
```bash
# Install Newman
npm install -g newman

# Run collection
newman run postman_collection.json \
  -e postman_environment.json \
  --reporters cli,json,html \
  --reporter-html-export newman-report.html

# View HTML report
open newman-report.html
```

## Test Scenarios

### 1. Health Check
- **Endpoint:** `GET /health`
- **Tests:** Status 200, correct response structure

### 2. Create Post
- **Endpoint:** `POST /posts/`
- **Tests:** Status 200, ID generated, correct data, views=0
- **Auto-saves:** `post_id` variable for subsequent requests

### 3. Get Post (Cache Miss)
- **Endpoint:** `GET /posts/{id}`
- **Tests:** Status 200, data structure, views incremented to 1
- **Note:** First read from database

### 4. Get Post (Cache Hit)
- **Endpoint:** `GET /posts/{id}`
- **Tests:** Status 200, faster response (<100ms), views still 1
- **Note:** Served from Redis cache

### 5. Get Post with Different IP
- **Endpoint:** `GET /posts/{id}`
- **Header:** `X-Forwarded-For: 192.168.1.100`
- **Tests:** Status 200, views incremented (unique IP)

### 6. Update Post
- **Endpoint:** `PUT /posts/{id}`
- **Tests:** Status 200, data updated, cache invalidated

### 7. Verify Update
- **Endpoint:** `GET /posts/{id}`
- **Tests:** Updated data returned (cache was invalidated)

### 8. Partial Update
- **Endpoint:** `PUT /posts/{id}`
- **Body:** Only `title` field
- **Tests:** Only title updated, other fields unchanged

### 9. Get All Posts
- **Endpoint:** `GET /posts/`
- **Tests:** Status 200, array response, contains posts

### 10. Pagination
- **Endpoint:** `GET /posts/?skip=0&limit=2`
- **Tests:** Status 200, respects limit parameter

### 11. Delete Post
- **Endpoint:** `DELETE /posts/{id}`
- **Tests:** Status 200, success message, cache invalidated

### 12. Verify Deletion
- **Endpoint:** `GET /posts/{id}`
- **Tests:** Status 404, error message

### 13-17. Error Handling
- Empty title validation (422)
- Missing fields validation (422)
- Non-existent post GET (404)
- Non-existent post UPDATE (404)
- Non-existent post DELETE (404)

## Test Execution Order

**Recommended order** (collection is pre-ordered):
1. Health Check
2. Create Post (saves `post_id`)
3. Get Post (Cache Miss)
4. Get Post (Cache Hit)
5. Get Post with Different IP
6. Update Post
7. Verify Update
8. Partial Update
9. Get All Posts
10. Pagination
11. Delete Post
12. Verify Deletion
13-17. Validation & Error Tests

## Environment Variables

### Default Values
```json
{
  "base_url": "http://localhost:8000",
  "post_id": ""
}
```

### Customization
To test against different environment:
1. Duplicate environment
2. Rename (e.g., "BlogCache Production")
3. Update `base_url` to production URL
4. Select new environment from dropdown

## Automated Test Assertions

Each request includes JavaScript tests that automatically verify:

```javascript
// Status code validation
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Response structure
pm.test("Response has correct structure", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
});

// Data integrity
pm.test("Post has correct data", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData.title).to.eql('Expected Title');
});

// Performance
pm.test("Response time is less than 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start services
        run: docker-compose -f docker-compose.local.yml up -d

      - name: Wait for API
        run: sleep 10

      - name: Install Newman
        run: npm install -g newman

      - name: Run Postman tests
        run: |
          newman run postman_collection.json \
            -e postman_environment.json \
            --reporters cli,json \
            --reporter-json-export newman-results.json

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: newman-results
          path: newman-results.json
```

## Troubleshooting

### Issue: Connection Refused
**Solution:** Ensure application is running:
```bash
docker-compose -f docker-compose.local.yml up
curl http://localhost:8000/health
```

### Issue: Tests Failing
**Solution:** Run requests in order (Create Post must run first to set `post_id`)

### Issue: Cache Tests Failing
**Solution:** Clear Redis cache:
```bash
docker exec -it blogcache-redis-1 redis-cli FLUSHDB
```

### Issue: View Counter Not Incrementing
**Solution:** Use different IP addresses via `X-Forwarded-For` header

## Advanced Usage

### Pre-request Scripts
Add to collection/request for dynamic data:
```javascript
// Generate random data
pm.collectionVariables.set("random_title",
    "Post " + Math.floor(Math.random() * 1000));
```

### Test Scripts
Add custom assertions:
```javascript
// Check response time
pm.test("Response time < 200ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(200);
});

// Validate schema
const schema = {
    type: "object",
    required: ["id", "title", "content"],
    properties: {
        id: { type: "number" },
        title: { type: "string" },
        content: { type: "string" }
    }
};
pm.test("Schema is valid", function () {
    pm.response.to.have.jsonSchema(schema);
});
```

## Performance Benchmarks

Expected response times:
- Health Check: < 50ms
- Create Post: < 200ms
- Get Post (Cache Miss): < 100ms
- Get Post (Cache Hit): < 50ms
- Update Post: < 200ms
- Delete Post: < 200ms

## License
MIT

## Author
Dmitrij Valedinskij
