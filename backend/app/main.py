from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import asyncio
from app.config import settings
from app.database import init_db, get_db, get_redis
from app.routers import auth, users, posts, uploads, static, health, github_auth
from app.services.image_cleanup import (
    start_image_cleanup_service,
    stop_image_cleanup_service,
)
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom JSON encoder to handle datetime with timezone
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Ensure datetime is in UTC
            if obj.tzinfo is None:
                # Assume naive datetime is UTC
                obj = obj.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if it has timezone
                obj = obj.astimezone(timezone.utc)
            return obj.isoformat()
        return super().default(obj)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events
    """
    # Startup
    try:
        # Temporarily skip database initialization for testing
        # init_db()
        logger.info("Database initialization skipped for testing")

        # Start image cleanup background service
        logger.info("Starting image cleanup background service...")
        # Note: Starting as a background task to avoid blocking startup
        asyncio.create_task(start_image_cleanup_service())

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Application shutdown - stopping background services...")
    stop_image_cleanup_service()
    logger.info("Application shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    description="SaladOverflow - A self-hosted discussion platform API",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(github_auth.router)  # GitHub OAuth
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(uploads.router)
app.include_router(static.router)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "Welcome to SaladOverflow API",
        "status": "running",
        "version": "1.0.0",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint for monitoring (public)

    Returns minimal information without exposing sensitive details.
    Use /health/detailed for comprehensive health information (requires auth).
    """
    from fastapi.responses import JSONResponse

    # Just check if the service is responsive
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": settings.app_name,
            "version": "1.0.0",
        },
        status_code=200,
    )


@app.get("/health/status")
async def health_status_check(
    db: Session = Depends(get_db), redis_client: redis.Redis = Depends(get_redis)
):
    """
    Component status health check (public, limited info)

    Checks health of components but doesn't expose sensitive configuration.
    """
    from fastapi.responses import JSONResponse

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "api": "operational",
            "database": "unknown",
            "cache": "unknown",
            "storage": "unknown",
        },
    }

    overall_healthy = True

    # Database check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "operational"
    except Exception:
        overall_healthy = False
        health_status["checks"]["database"] = "unavailable"

    # Redis check
    try:
        test_key = "health_check_test"
        redis_client.setex(test_key, 5, "ok")
        result = redis_client.get(test_key)
        redis_client.delete(test_key)
        health_status["checks"]["cache"] = "operational" if result else "degraded"
    except Exception:
        health_status["checks"]["cache"] = "unavailable"

    # Storage check
    try:
        uploads_dir = Path("uploads/images")
        if uploads_dir.exists() and os.access("uploads", os.W_OK):
            health_status["checks"]["storage"] = "operational"
        else:
            overall_healthy = False
            health_status["checks"]["storage"] = "unavailable"
    except Exception:
        overall_healthy = False
        health_status["checks"]["storage"] = "unavailable"

    health_status["status"] = "healthy" if overall_healthy else "degraded"
    status_code = 200 if overall_healthy else 503

    return JSONResponse(content=health_status, status_code=status_code)


# API info endpoint
@app.get(f"/api/{settings.api_version}/info")
async def api_info():
    """
    API information endpoint
    """
    return {
        "api_version": settings.api_version,
        "app_name": settings.app_name,
        "debug_mode": settings.debug,
        "endpoints": {"health": "/health", "docs": "/docs", "redoc": "/redoc"},
    }
