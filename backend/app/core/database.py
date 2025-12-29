"""
Database connection and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    Yields a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("database_session_error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set connection-level settings if needed"""
    pass


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("database_initialized")

