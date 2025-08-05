"""
Database initialization script for POORNASREE AI Platform
"""
import asyncio
import logging
import re
import ssl
import pymysql
from sqlalchemy import text, create_engine
from sqlalchemy.exc import OperationalError

from app.core.database import engine, SessionLocal, Base
from app.core.config import settings
from app.models import *  # Import all models to register them

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_database_if_not_exists():
    """Create database if it doesn't exist using direct PyMySQL connection"""
    try:
        # Extract database name from URL
        database_url = str(engine.url)
        match = re.search(r'/([^/?]+)(?:\?|$)', database_url)
        if not match:
            raise ValueError("Could not extract database name from URL")
        
        database_name = match.group(1)
        logger.info(f"Database name extracted: {database_name}")
        
        # Use direct PyMySQL connection for database creation
        import ssl
        import pymysql
        
        # Connection parameters
        connection_params = {
            'host': 'psrazuredb.mysql.database.azure.com',
            'port': 3306,
            'user': 'psrcloud',
            'password': 'Access@LRC2404',  # Direct password without encoding
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # Add SSL for Azure MySQL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connection_params['ssl'] = ssl_context
        logger.info("Using SSL for Azure MySQL connection")
        
        # Connect to MySQL server (without specifying database)
        logger.info(f"Connecting to server: {connection_params['host']}")
        connection = pymysql.connect(**connection_params)
        
        try:
            with connection.cursor() as cursor:
                # Check if database exists
                logger.info(f"Checking if database '{database_name}' exists...")
                cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
                result = cursor.fetchone()
                
                if result is None:
                    # Database doesn't exist, create it
                    logger.info(f"Creating database: {database_name}")
                    cursor.execute(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"✅ Database '{database_name}' created successfully")
                else:
                    logger.info(f"✅ Database '{database_name}' already exists")
                
                # Verify database was created/exists
                cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
                result = cursor.fetchone()
                
                if result is not None:
                    logger.info(f"✅ Database '{database_name}' is ready for use")
                    return True
                else:
                    logger.error(f"❌ Database '{database_name}' verification failed")
                    return False
                    
        finally:
            connection.close()
            logger.info("Database creation connection closed")
        
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        raise


async def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        
        # Test database connection
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()
            if test_value and test_value[0] == 1:
                logger.info("Database connection test successful")
            else:
                logger.error("Database connection test failed")
                
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def create_admin_user():
    """Create default admin user if not exists"""
    try:
        from app.models.user import User, UserRoleEnum, UserStatusEnum
        
        with SessionLocal() as db:
            # Check if admin exists
            admin_exists = db.query(User).filter(
                User.email == settings.admin_email,
                User.role == UserRoleEnum.ADMIN
            ).first()
            
            if not admin_exists:
                logger.info(f"Creating admin user: {settings.admin_email}")
                
                admin_user = User(
                    email=settings.admin_email,
                    full_name="System Administrator",
                    role=UserRoleEnum.ADMIN,
                    status=UserStatusEnum.ACTIVE,
                    is_active=True,
                    is_verified=True
                )
                
                db.add(admin_user)
                db.commit()
                
                logger.info("Admin user created successfully")
            else:
                logger.info("Admin user already exists")
                
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise


async def create_sample_categories():
    """Create sample document categories"""
    try:
        from app.models.knowledge_base import DocumentCategory, KnowledgeBaseTierEnum
        
        sample_categories = [
            {
                "name": "User Manuals",
                "description": "End-user operation manuals and guides",
                "knowledge_base_tiers": [KnowledgeBaseTierEnum.CUSTOMER.value, KnowledgeBaseTierEnum.ENGINEER.value, KnowledgeBaseTierEnum.ADMIN.value],
                "path": "/user-manuals",
                "level": 0,
                "icon": "📖",
                "color": "#4CAF50"
            },
            {
                "name": "Technical Documentation",
                "description": "Technical specifications and service manuals",
                "knowledge_base_tiers": [KnowledgeBaseTierEnum.ENGINEER.value, KnowledgeBaseTierEnum.ADMIN.value],
                "path": "/technical-docs",
                "level": 0,
                "icon": "🔧",
                "color": "#2196F3"
            },
            {
                "name": "Safety Protocols",
                "description": "Safety procedures and compliance documents",
                "knowledge_base_tiers": [KnowledgeBaseTierEnum.CUSTOMER.value, KnowledgeBaseTierEnum.ENGINEER.value, KnowledgeBaseTierEnum.ADMIN.value],
                "path": "/safety-protocols",
                "level": 0,
                "icon": "⚠️",
                "color": "#FF9800"
            },
            {
                "name": "Troubleshooting Guides",
                "description": "Problem diagnosis and resolution guides",
                "knowledge_base_tiers": [KnowledgeBaseTierEnum.CUSTOMER.value, KnowledgeBaseTierEnum.ENGINEER.value, KnowledgeBaseTierEnum.ADMIN.value],
                "path": "/troubleshooting",
                "level": 0,
                "icon": "🔍",
                "color": "#9C27B0"
            },
            {
                "name": "Maintenance Procedures",
                "description": "Preventive and corrective maintenance procedures",
                "knowledge_base_tiers": [KnowledgeBaseTierEnum.ENGINEER.value, KnowledgeBaseTierEnum.ADMIN.value],
                "path": "/maintenance",
                "level": 0,
                "icon": "🛠️",
                "color": "#607D8B"
            }
        ]
        
        with SessionLocal() as db:
            for category_data in sample_categories:
                # Check if category exists
                existing_category = db.query(DocumentCategory).filter(
                    DocumentCategory.name == category_data["name"]
                ).first()
                
                if not existing_category:
                    category = DocumentCategory(**category_data)
                    db.add(category)
                    logger.info(f"Created category: {category_data['name']}")
            
            db.commit()
            logger.info("Sample categories created successfully")
            
    except Exception as e:
        logger.error(f"Failed to create sample categories: {e}")
        raise


async def initialize_knowledge_base_stats():
    """Initialize knowledge base statistics"""
    try:
        from app.models.knowledge_base import KnowledgeBaseStats, KnowledgeBaseTierEnum
        
        with SessionLocal() as db:
            # Create initial stats for each tier
            for tier in KnowledgeBaseTierEnum:
                existing_stats = db.query(KnowledgeBaseStats).filter(
                    KnowledgeBaseStats.knowledge_base_tier == tier
                ).first()
                
                if not existing_stats:
                    stats = KnowledgeBaseStats(
                        knowledge_base_tier=tier,
                        total_documents=0,
                        total_chunks=0,
                        total_words=0,
                        total_size_bytes=0
                    )
                    db.add(stats)
                    logger.info(f"Created stats for tier: {tier.name}")
            
            db.commit()
            logger.info("Knowledge base statistics initialized")
            
    except Exception as e:
        logger.error(f"Failed to initialize knowledge base stats: {e}")
        raise


async def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    try:
        # Step 1: Create database if it doesn't exist
        logger.info("Step 1: Checking/Creating database...")
        await create_database_if_not_exists()
        
        # Step 2: Create tables
        logger.info("Step 2: Creating database tables...")
        await create_tables()
        
        # Step 3: Create admin user
        logger.info("Step 3: Creating admin user...")
        await create_admin_user()
        
        # Step 4: Create sample categories
        logger.info("Step 4: Creating sample categories...")
        await create_sample_categories()
        
        # Step 5: Initialize KB stats
        logger.info("Step 5: Initializing knowledge base stats...")
        await initialize_knowledge_base_stats()
        
        logger.info("🎉 Database initialization completed successfully!")
        logger.info("✅ Your POORNASREE AI Platform database is ready!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        # Close database connections
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
