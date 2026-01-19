"""Database configuration and session management.

This module handles database connections, session creation, and initialization.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models import Base


# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before using
)


# Enable foreign keys for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_session() -> Generator[Session, None, None]:
    """Get a database session.
    
    This is the primary way to get a database session throughout the application.
    Use as a context manager or dependency injection.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        with get_session() as session:
            user = session.query(User).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_session_context():
    """Get a database session as a context manager.
    
    Returns:
        Session: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize the database.
    
    Creates all tables defined in models.
    This should be called once on application startup.
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {settings.database_url}")


def drop_db() -> None:
    """Drop all database tables.
    
    ⚠️ WARNING: This will delete all data!
    Only use for testing or development.
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")


def reset_db() -> None:
    """Reset the database by dropping and recreating all tables.
    
    ⚠️ WARNING: This will delete all data!
    Only use for testing or development.
    """
    drop_db()
    init_db()
    print("✅ Database reset complete")
