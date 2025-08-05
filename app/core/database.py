"""
Database configuration and session management for POORNASREE AI Platform
"""
# pylint: disable=import-error,no-name-in-module
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
# SSL configuration for Azure MySQL
connect_args = {
    "charset": "utf8mb4",
    "autocommit": False,
}

# Add SSL configuration for Azure MySQL
database_url_str = str(settings.database_url)
if "azure" in database_url_str or "mysql.database.azure.com" in database_url_str:
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args.update({
        "ssl": ssl_context,
    })

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args
)

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """
    Initialize database tables
    """
    try:
        # Import all models to ensure they are registered with SQLAlchemy
        from app.models import user, knowledge_base, analytics, training
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """
    Close database connections
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


class DatabaseManager:
    """Database manager for handling connections and transactions"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: dict = None):
        """Execute a raw SQL query"""
        with self.get_session() as session:
            try:
                result = session.execute(query, params or {})
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                logger.error(f"Query execution error: {e}")
                raise
    
    def bulk_insert(self, model_class, data_list: list):
        """Bulk insert data"""
        with self.get_session() as session:
            try:
                session.bulk_insert_mappings(model_class, data_list)
                session.commit()
                logger.info(f"Bulk inserted {len(data_list)} records")
            except Exception as e:
                session.rollback()
                logger.error(f"Bulk insert error: {e}")
                raise


# Global database manager instance
db_manager = DatabaseManager()
