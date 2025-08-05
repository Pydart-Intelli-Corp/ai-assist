#!/usr/bin/env python3
"""
Database checker script for POORNASREE AI Platform
Checks available databases and permissions
"""
import logging
import ssl
import pymysql
from urllib.parse import urlparse
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_database_url(url: str):
    """Parse database URL to extract connection components"""
    parsed = urlparse(url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 3306,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/') if parsed.path else None,
        'scheme': parsed.scheme
    }


def check_database_access():
    """Check what databases are available and what permissions we have"""
    try:
        # Parse the database URL
        db_config = parse_database_url(str(settings.database_url))
        
        logger.info(f"Checking database access for user: {db_config['user']}")
        logger.info(f"Target database: {db_config['database']}")
        
        # Connection parameters without database name
        connection_params = {
            'host': db_config['host'],
            'port': db_config['port'],
            'user': db_config['user'],
            'password': db_config['password'],
            'charset': 'utf8mb4'
        }
        
        # Add SSL for Azure MySQL
        if "azure" in db_config['host'] or "mysql.database.azure.com" in db_config['host']:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connection_params['ssl'] = ssl_context
            logger.info("Using SSL for Azure MySQL connection")
        
        # Try connecting without specifying database first
        try:
            connection = pymysql.connect(**connection_params)
            logger.info(f"✅ Connected to MySQL server at {db_config['host']}")
            
            with connection.cursor() as cursor:
                # Check MySQL version
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                logger.info(f"MySQL Version: {version[0]}")
                
                # Check current user
                cursor.execute("SELECT USER()")
                user = cursor.fetchone()
                logger.info(f"Connected as: {user[0]}")
                
                # List available databases
                logger.info("\n--- Available Databases ---")
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                for db in databases:
                    logger.info(f"  - {db[0]}")
                
                # Check if target database exists
                target_db = db_config['database']
                cursor.execute("SHOW DATABASES LIKE %s", (target_db,))
                result = cursor.fetchone()
                
                if result:
                    logger.info(f"\n✅ Target database '{target_db}' exists!")
                    
                    # Try to connect to the specific database
                    connection.close()
                    
                    # Connect to specific database
                    connection_params['database'] = target_db
                    connection = pymysql.connect(**connection_params)
                    logger.info(f"✅ Successfully connected to database '{target_db}'")
                    
                    with connection.cursor() as cursor:
                        # Check tables in database
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        
                        if tables:
                            logger.info(f"\n--- Tables in '{target_db}' ---")
                            for table in tables:
                                logger.info(f"  - {table[0]}")
                        else:
                            logger.info(f"\n📝 Database '{target_db}' is empty (no tables)")
                    
                    return True
                    
                else:
                    logger.warning(f"\n⚠️  Target database '{target_db}' does not exist")
                    
                    # Check if we can create it
                    try:
                        cursor.execute(f"CREATE DATABASE `{target_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        logger.info(f"✅ Successfully created database '{target_db}'")
                        return True
                    except Exception as create_error:
                        logger.error(f"❌ Cannot create database '{target_db}': {create_error}")
                        return False
            
            connection.close()
            
        except Exception as conn_error:
            logger.error(f"❌ Connection failed: {conn_error}")
            return False
            
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False


def main():
    """Main function"""
    logger.info("="*60)
    logger.info("🔍 POORNASREE AI Platform - Database Access Check")
    logger.info("="*60)
    
    success = check_database_access()
    
    logger.info("\n" + "="*60)
    if success:
        logger.info("✅ SUCCESS: Database access verified!")
        logger.info("You can proceed with table creation.")
    else:
        logger.info("❌ FAILED: Database access issues detected")
        logger.info("Please check the database configuration or permissions.")
    logger.info("="*60)
    
    return success


if __name__ == "__main__":
    main()
