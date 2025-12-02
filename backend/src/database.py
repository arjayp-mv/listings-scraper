# =============================================================================
# Amazon Reviews Scraper - Database Connection
# =============================================================================
# Purpose: SQLAlchemy engine and session management
# Public API: engine, SessionLocal, get_db()
# Dependencies: sqlalchemy, config
# =============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings


# ===== Engine Configuration =====
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo=False,          # Set True for SQL debugging
)

# ===== Session Factory =====
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ===== Base Class for Models =====
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.

    Yields database session and ensures cleanup after request.
    Used with FastAPI's Depends() for route injection.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
