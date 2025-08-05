"""
Main FastAPI application for POORNASREE AI Platform
"""
# pylint: disable=import-error,logging-fstring-interpolation,broad-exception-caught,wrong-import-order

import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.auth.auth import router as auth_router
from app.api.query.query import router as query_router
from app.api.documents.documents import router as documents_router
from app.api.training.training import router as training_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),  # pylint: disable=no-member
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    logger.info("Starting POORNASREE AI Platform...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    yield

    # Shutdown
    logger.info("Shutting down POORNASREE AI Platform...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error during shutdown: %s", e)


# Create FastAPI application
app = FastAPI(
    title=settings.platform_name,
    version=settings.platform_version,
    description="Comprehensive AI platform for machine maintenance and technical support",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add trusted host middleware (security)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add processing time header to responses
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all requests for monitoring
    """
    start_time = time.time()

    # Log request
    logger.info("Request: %s %s", request.method, request.url.path)

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "Response: %s (%.3fs) %s %s",
            response.status_code, process_time, request.method, request.url.path
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed: %s %s (%.3fs) - %s",
            request.method, request.url.path, process_time, str(e)
        )
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler
    """
    logger.warning("HTTP %s: %s - %s %s", exc.status_code, exc.detail, request.method, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler for unexpected errors
    """
    logger.error("Unexpected error: %s - %s %s", str(exc), request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "InternalServerError"
            }
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "platform": settings.platform_name,
        "version": settings.platform_version,
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """
    Root endpoint with platform information
    """
    return {
        "platform": settings.platform_name,
        "version": settings.platform_version,
        "description": "Comprehensive AI platform for machine maintenance and technical support",
        "api_version": settings.api_version,
        "docs_url": "/docs" if settings.debug else "Documentation not available in production",
        "health_check": "/health"
    }


# Include routers
app.include_router(auth_router, prefix=f"/{settings.api_version}")
app.include_router(query_router, prefix=f"/{settings.api_version}")
app.include_router(documents_router, prefix=f"/{settings.api_version}")
app.include_router(training_router, prefix=f"/{settings.api_version}")

# Future routers will be added here
# app.include_router(analytics_router, prefix=f"/{settings.api_version}")
# app.include_router(admin_router, prefix=f"/{settings.api_version}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()  # pylint: disable=no-member
    )
