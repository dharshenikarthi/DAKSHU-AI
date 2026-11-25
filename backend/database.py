from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

# Handle SQLite vs PostgreSQL configuration with resilient fallback
def create_app_engine():
    db_url = settings.DATABASE_URL
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    try:
        eng = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
        with eng.connect() as conn:
            pass
        return eng
    except Exception:
        # Fallback to /tmp on serverless environments
        try:
            return create_engine("sqlite:////tmp/dakshu.db", connect_args={"check_same_thread": False}, pool_pre_ping=True)
        except Exception:
            return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, pool_pre_ping=True)

engine = create_app_engine()

# Enable Foreign Key support in SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

