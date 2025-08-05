"""
Simple database connection test for POORNASREE AI Platform
"""
# pylint: disable=no-member
import asyncio
import logging
import pytest
from sqlalchemy import create_engine, text
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_database_connection():
    """Test basic database connection"""
    try:
        logger.info("Testing database connection...")
        logger.info(f"Connecting to: {settings.database_url.replace('Access%40LRC2404', '***')}")
        
        # Create engine with SSL settings
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connect_args = {
            "charset": "utf8mb4",
            "autocommit": False,
            "ssl": ssl_context,
        }
        
        engine = create_engine(
            settings.database_url,
            echo=True,
            connect_args=connect_args
        )
        
        # Test connection
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            logger.info(f"Connection successful! Test query result: {row[0]}")
            
            # Show databases
            result = connection.execute(text("SHOW DATABASES"))
            databases = [row[0] for row in result.fetchall()]
            logger.info(f"Available databases: {databases}")
            
            # Check current database
            result = connection.execute(text("SELECT DATABASE() as current_db"))
            current_db = result.fetchone()
            logger.info(f"Current database: {current_db[0]}")
            
        engine.dispose()
        logger.info("Database connection test completed successfully!")
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_database_connection())
