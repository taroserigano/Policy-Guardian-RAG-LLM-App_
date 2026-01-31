"""
Database session management.
Provides SQLAlchemy engine and session factory with dependency injection support.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with robust connection pooling
# These settings help prevent connection issues and server crashes
try:
    # Extract connection args based on database type
    connect_args = {}
    if "postgresql" in settings.database_url or "postgres" in settings.database_url:
        # PostgreSQL-specific settings for production reliability
        connect_args = {
            "options": "-c statement_timeout=30000",  # 30 second query timeout
            "connect_timeout": 10,  # 10 second connection timeout
        }
    elif "sqlite" in settings.database_url:
        # SQLite-specific settings
        connect_args = {
            "check_same_thread": False,
            "timeout": 30,
        }
    
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_pre_ping=True,       # Check connection validity before use
        pool_size=10,             # Increased from 5 to 10 for production
        max_overflow=20,          # Increased from 10 to 20 for burst traffic
        pool_timeout=30,          # Wait up to 30s for a connection
        pool_recycle=1800,        # Recycle connections every 30 minutes
        echo=settings.debug,      # Log SQL queries in debug mode
        connect_args=connect_args # Database-specific connection arguments
    )
    # Session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    DB_AVAILABLE = True
    logger.info("Database engine created with connection pooling")
except Exception as e:
    logger.warning(f"Database not available: {e}")
    engine = None
    SessionLocal = None
    DB_AVAILABLE = False

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator[Optional[Session], None, None]:
    """
    Dependency injection function for FastAPI routes.
    Creates a new database session for each request with proper cleanup.
    
    Features:
    - Automatic rollback on error
    - Guaranteed session closure
    - Connection pool management
    
    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Database session that is automatically closed after use, or None if DB not available
    """
    if not DB_AVAILABLE or SessionLocal is None:
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Rollback on any exception to prevent partial commits
        logger.error(f"Database error, rolling back: {e}")
        db.rollback()
        raise
    finally:
        # Always close the session to return connection to pool
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database session: {e}")


def get_db_context():
    """
    Context manager for manual database session management outside of FastAPI.
    Use this for background tasks, CLI scripts, or streaming generators.
    
    Usage:
        from app.db.session import get_db_context
        
        with get_db_context() as db:
            if db:
                items = db.query(Item).all()
    """
    if not DB_AVAILABLE or SessionLocal is None:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error in context, rolling back: {e}")
        db.rollback()
        raise
    finally:
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database context: {e}")


def get_pool_status() -> dict:
    """
    Get current connection pool statistics for monitoring.
    
    Returns:
        Dictionary with pool metrics:
        - size: Configured pool size
        - checked_in: Connections currently in the pool
        - checked_out: Connections currently in use
        - overflow: Overflow connections created beyond pool_size
        - max_overflow: Maximum overflow allowed
    """
    if not DB_AVAILABLE or engine is None:
        return {"available": False}
    
    try:
        pool = engine.pool
        return {
            "available": True,
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": pool._max_overflow,
            "total_connections": pool.checkedin() + pool.checkedout(),
            "utilization_percent": round((pool.checkedout() / (pool.size() + pool._max_overflow)) * 100, 2)
        }
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        return {"available": True, "error": str(e)}


def log_pool_status():
    """
    Log current connection pool status for monitoring.
    Call this periodically or when investigating connection issues.
    """
    status = get_pool_status()
    if status.get("available"):
        if "error" not in status:
            logger.info(
                f"Connection Pool Status: "
                f"{status['checked_out']}/{status['size']} in use, "
                f"{status['overflow']} overflow, "
                f"{status['utilization_percent']}% utilized"
            )
        else:
            logger.warning(f"Connection pool status error: {status['error']}")
    else:
        logger.info("Database not available")
