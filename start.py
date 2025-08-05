"""
Startup script for POORNASREE AI Platform
"""
# pylint: disable=no-member
import asyncio
import subprocess
import sys
import os
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all required packages are installed"""
    logger.info("Checking requirements...")
    
    try:
        # Check if requirements.txt exists
        requirements_file = Path("requirements.txt")
        if not requirements_file.exists():
            logger.error("requirements.txt not found!")
            return False
        
        # Try importing key packages
        import fastapi
        import uvicorn
        import sqlalchemy
        import weaviate
        import google.generativeai
        
        logger.info("✅ All required packages are available")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.info("Please run: pip install -r requirements.txt")
        return False


def check_environment():
    """Check environment configuration"""
    logger.info("Checking environment configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        logger.error("❌ .env file not found!")
        logger.info("Please create .env file with required configuration")
        return False
    
    # Check critical environment variables
    from app.core.config import settings
    
    try:
        critical_vars = [
            settings.database_url,
            settings.secret_key,
            settings.admin_email,
            settings.weaviate_url,
            settings.weaviate_api_key,
            settings.google_api_key
        ]
        
        logger.info("✅ Environment configuration is valid")
        return True
        
    except Exception as e:
        logger.error(f"❌ Environment configuration error: {e}")
        return False


async def initialize_database():
    """Initialize database"""
    logger.info("Initializing database...")
    
    try:
        # Run database initialization
        from init_db import main as init_db_main
        await init_db_main()
        logger.info("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


def start_server():
    """Start the FastAPI server"""
    logger.info("Starting POORNASREE AI Platform server...")
    
    try:
        import uvicorn
        from app.core.config import settings
        
        # Start the server
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        return False


async def run_tests():
    """Run API tests"""
    logger.info("Running API tests...")
    
    try:
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        from test_api import APITester
        tester = APITester()
        success = await tester.run_all_tests()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ API tests failed: {e}")
        return False


async def main():
    """Main startup function"""
    logger.info("🚀 POORNASREE AI Platform - Startup Script")
    logger.info("=" * 60)
    
    # Step 1: Check requirements
    if not check_requirements():
        logger.error("❌ Requirements check failed")
        sys.exit(1)
    
    # Step 2: Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        sys.exit(1)
    
    # Step 3: Initialize database
    if not await initialize_database():
        logger.error("❌ Database initialization failed")
        sys.exit(1)
    
    logger.info("✅ All startup checks passed!")
    logger.info("\n" + "=" * 60)
    logger.info("🎯 POORNASREE AI Platform is ready to start!")
    logger.info("=" * 60)
    
    print("\nChoose an option:")
    print("1. Start server")
    print("2. Run tests only")
    print("3. Start server and run tests")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        logger.info("Starting server...")
        start_server()
        
    elif choice == "2":
        logger.info("Running tests...")
        success = await run_tests()
        if success:
            logger.info("✅ All tests passed!")
        else:
            logger.error("❌ Some tests failed!")
            
    elif choice == "3":
        logger.info("Starting server and running tests...")
        # Start server in background and run tests
        import threading
        
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to start
        await asyncio.sleep(5)
        
        # Run tests
        success = await run_tests()
        if success:
            logger.info("✅ All tests passed! Server is running...")
            input("Press Enter to stop the server...")
        else:
            logger.error("❌ Some tests failed!")
            
    elif choice == "4":
        logger.info("Exiting...")
        sys.exit(0)
        
    else:
        logger.error("Invalid choice!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)
