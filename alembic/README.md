# Alembic Database Migrations

## Commands

### Create a new migration
```bash
# Auto-generate from model changes
poetry run alembic revision --autogenerate -m "description"

# Manual migration
poetry run alembic revision -m "description"
```

### Apply migrations
```bash
# Upgrade to latest
poetry run alembic upgrade head

# Upgrade one version
poetry run alembic upgrade +1

# Downgrade one version
poetry run alembic downgrade -1

# Downgrade to specific revision
poetry run alembic downgrade <revision_id>
```

### Check status
```bash
# Show current revision
poetry run alembic current

# Show migration history
poetry run alembic history

# Show pending migrations
poetry run alembic heads
```

### Docker usage
```bash
# Run migrations in container
docker-compose -f docker-compose.local.yml exec app alembic upgrade head

# Create migration in container
docker-compose -f docker-compose.local.yml exec app alembic revision --autogenerate -m "description"
```

## Migration File Naming

Format: `YYYYMMDD_HHMM-<revision>_<slug>.py`

Example: `20260307_1613-f8df674c63ab_create_posts_table.py`
