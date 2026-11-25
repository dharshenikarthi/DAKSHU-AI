# Database Migrations

DAKSHU AI utilizes SQLAlchemy ORM with automatic table generation on startup (`Base.metadata.create_all(bind=engine)`).

For enterprise schema evolution in production, Alembic migrations can be configured:

```bash
# Initialize Alembic (optional)
alembic init backend/migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

