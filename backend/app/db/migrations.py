"""
Simple database migration management.
For MVP, we use SQLAlchemy's create_all(). 
For production, consider using Alembic for proper migrations.
"""
from app.db.session import engine, Base
from app.db.models import Document, ChatAudit
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    """
    Create all database tables.
    This is called at application startup.
    
    Note: This uses create_all() which is fine for development.
    For production, use Alembic migrations:
        - alembic init migrations
        - alembic revision --autogenerate -m "Initial migration"
        - alembic upgrade head
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_all_tables() -> None:
    """
    Drop all database tables.
    USE WITH CAUTION - This deletes all data!
    Only for development/testing.
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")
