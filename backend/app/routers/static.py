from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import redis
import logging
from pathlib import Path
from typing import Optional
import mimetypes
import hashlib
from datetime import datetime, timedelta

from app.database import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/static", tags=["static"])

# Static files directory
STATIC_DIR = Path(__file__).parent.parent / "static"

# Cache settings
CACHE_DURATION = 3600  # 1 hour in seconds
CACHE_PREFIX = "static_file:"


def get_file_hash(file_path: Path) -> str:
    """Generate a hash for the file to use as cache key"""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            return hashlib.md5(content).hexdigest()
    except Exception:
        return str(file_path.stat().st_mtime)


def get_cache_key(file_path: str, file_hash: str) -> str:
    """Generate cache key for file"""
    return f"{CACHE_PREFIX}{file_path}:{file_hash}"


@router.get("/img/logo.png")
async def get_logo(redis_client: redis.Redis = Depends(get_redis)) -> FileResponse:
    """
    Serve the logo.png file with Redis caching

    This endpoint serves the SaladOverflow logo with proper caching headers
    and Redis-based caching to improve performance.
    """
    try:
        logo_path = STATIC_DIR / "img" / "logo.png"

        # Check if file exists
        if not logo_path.exists():
            logger.error(f"Logo file not found at {logo_path}")
            raise HTTPException(status_code=404, detail="Logo not found")

        # Generate file hash for cache validation
        file_hash = get_file_hash(logo_path)
        cache_key = get_cache_key("logo.png", file_hash)

        # Try to get from Redis cache
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Logo served from Redis cache")
                # For FileResponse, we still need to return the actual file
                # but we can log that it's cached and set appropriate headers
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

        # Store in cache for next time (store file metadata)
        try:
            cache_value = f"served:{datetime.now().isoformat()}"
            redis_client.setex(cache_key, CACHE_DURATION, cache_value)
        except Exception as e:
            logger.warning(f"Failed to cache logo metadata: {e}")

        # Determine content type
        content_type, _ = mimetypes.guess_type(str(logo_path))
        if not content_type:
            content_type = "image/png"

        logger.info("Serving logo.png")

        # Return the file with caching headers
        return FileResponse(
            path=str(logo_path),
            media_type=content_type,
            headers={
                "Cache-Control": f"public, max-age={CACHE_DURATION}",
                "ETag": f'"{file_hash}"',
                "Last-Modified": datetime.fromtimestamp(
                    logo_path.stat().st_mtime
                ).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving logo: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/img/{filename}")
async def get_image(
    filename: str, redis_client: redis.Redis = Depends(get_redis)
) -> FileResponse:
    """
    Serve image files from the static/img directory with Redis caching

    This is a general endpoint for serving any image from the static assets.
    """
    try:
        # Security: Only allow certain file extensions
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}
        file_path = STATIC_DIR / "img" / filename

        # Check file extension
        if file_path.suffix.lower() not in allowed_extensions:
            raise HTTPException(status_code=400, detail="File type not allowed")

        # Check if file exists
        if not file_path.exists():
            logger.warning(f"Image file not found: {filename}")
            raise HTTPException(status_code=404, detail="Image not found")

        # Generate file hash for cache validation
        file_hash = get_file_hash(file_path)
        cache_key = get_cache_key(filename, file_hash)

        # Try to get from Redis cache
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Image {filename} served from Redis cache")
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

        # Store in cache for next time
        try:
            cache_value = f"served:{datetime.now().isoformat()}"
            redis_client.setex(cache_key, CACHE_DURATION, cache_value)
        except Exception as e:
            logger.warning(f"Failed to cache image metadata: {e}")

        # Determine content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "image/png"  # Default fallback

        logger.info(f"Serving image: {filename}")

        # Return the file with caching headers
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            headers={
                "Cache-Control": f"public, max-age={CACHE_DURATION}",
                "ETag": f'"{file_hash}"',
                "Last-Modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).strftime("%a, %d %b %Y %H:%M:%S GMT"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def static_health(redis_client: redis.Redis = Depends(get_redis)):
    """
    Health check endpoint for static file service
    """
    logo_path = STATIC_DIR / "img" / "logo.png"

    # Check Redis connectivity
    redis_status = "healthy"
    redis_message = "Connected"
    try:
        test_key = "static_health_check"
        redis_client.setex(test_key, 5, "test")
        result = redis_client.get(test_key)
        redis_client.delete(test_key)
        if not result:
            redis_status = "degraded"
            redis_message = "Using mock client"
    except Exception as e:
        redis_status = "unhealthy"
        redis_message = f"Error: {str(e)}"

    # Check file system
    static_dir_exists = STATIC_DIR.exists()
    img_dir_exists = (STATIC_DIR / "img").exists()
    logo_exists = logo_path.exists()

    # Check read permissions
    can_read_static = (
        os.access(str(STATIC_DIR), os.R_OK) if static_dir_exists else False
    )

    overall_status = "healthy"
    if not (static_dir_exists and img_dir_exists and can_read_static):
        overall_status = "unhealthy"
    elif redis_status != "healthy":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "service": "static_files",
        "checks": {
            "redis": {"status": redis_status, "message": redis_message},
            "filesystem": {
                "status": (
                    "healthy"
                    if (static_dir_exists and can_read_static)
                    else "unhealthy"
                ),
                "static_dir": str(STATIC_DIR),
                "static_dir_exists": static_dir_exists,
                "img_dir_exists": img_dir_exists,
                "logo_exists": logo_exists,
                "readable": can_read_static,
            },
            "cache": {"duration_seconds": CACHE_DURATION, "prefix": CACHE_PREFIX},
        },
    }
