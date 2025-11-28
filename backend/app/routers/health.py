from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import os
from pathlib import Path
from datetime import datetime
import logging

from app.database import get_db, get_redis
from app.config import settings
from app.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Detailed health check with individual component status (REQUIRES AUTHENTICATION)

    ⚠️ SECURITY: This endpoint exposes sensitive system information and requires authentication.

    Returns comprehensive health information for all system components.
    Useful for monitoring dashboards and alerting systems.

    Only accessible to authenticated users. In production, this should be restricted to admin users only.
    """
    # Additional security: Check if user is admin (if you have admin role)
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": "development" if settings.debug else "production",
        "checks": {},
        "requested_by": current_user.username,
    }

    overall_healthy = True

    # 1. Database Health Check
    try:
        # Test basic query
        db.execute(text("SELECT 1"))

        # Test database version
        result = db.execute(text("SELECT VERSION()"))
        db_version = result.scalar()

        # Don't expose full connection string - just host
        db_host = "configured"
        if "@" in settings.database_url:
            db_host = settings.database_url.split("@")[1].split("/")[0]

        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
            "details": {
                "type": "MariaDB/MySQL",
                "version": db_version[:50] if db_version else "unknown",
                "host": db_host,  # Don't expose credentials
            },
        }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }

    # 2. Redis Health Check
    try:
        # Try to set and get a test value
        test_key = "health_check_detailed_test"
        redis_client.setex(test_key, 10, "ok")
        result = redis_client.get(test_key)
        redis_client.delete(test_key)

        if result:
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "message": "Redis cache is operational",
                "details": {"type": "Redis", "connection": "active"},
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "message": "Redis available but using mock client",
                "details": {"type": "Mock", "connection": "fallback"},
            }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }

    # 3. File System Health Check
    try:
        uploads_dir = Path("uploads/images")
        static_dir = Path("app/static/img")
        docs_dir = Path("docs")

        # Check existence
        uploads_exists = uploads_dir.exists()
        static_exists = static_dir.exists()

        # Check permissions
        uploads_writable = (
            os.access("uploads", os.W_OK) if os.path.exists("uploads") else False
        )
        uploads_readable = (
            os.access("uploads", os.R_OK) if os.path.exists("uploads") else False
        )
        static_readable = (
            os.access("app/static", os.R_OK) if os.path.exists("app/static") else False
        )

        # Count files
        upload_count = len(list(uploads_dir.glob("*"))) if uploads_exists else 0
        static_count = len(list(static_dir.glob("*"))) if static_exists else 0

        if uploads_exists and static_exists and uploads_writable and uploads_readable:
            health_status["checks"]["filesystem"] = {
                "status": "healthy",
                "message": "File system accessible and writable",
                "details": {
                    "uploads": {
                        "path": str(uploads_dir),
                        "exists": uploads_exists,
                        "readable": uploads_readable,
                        "writable": uploads_writable,
                        "file_count": upload_count,
                    },
                    "static": {
                        "path": str(static_dir),
                        "exists": static_exists,
                        "readable": static_readable,
                        "file_count": static_count,
                    },
                },
            }
        else:
            overall_healthy = False
            health_status["checks"]["filesystem"] = {
                "status": "unhealthy",
                "message": "File system issues detected",
                "details": {
                    "uploads_exists": uploads_exists,
                    "static_exists": static_exists,
                    "uploads_writable": uploads_writable,
                },
            }
    except Exception as e:
        overall_healthy = False
        health_status["checks"]["filesystem"] = {
            "status": "unhealthy",
            "message": f"File system check failed: {str(e)}",
        }

    # 4. Email Service Health Check
    try:
        from app.services.email_service import email_service

        if email_service.is_email_configured():
            # Don't expose full email/credentials
            smtp_host_masked = (
                settings.smtp_host if settings.smtp_host else "not configured"
            )
            from_email_masked = (
                settings.smtp_from_email.split("@")[0][:3]
                + "***@"
                + settings.smtp_from_email.split("@")[1]
                if settings.smtp_from_email and "@" in settings.smtp_from_email
                else "not configured"
            )

            health_status["checks"]["email"] = {
                "status": "healthy",
                "message": "Email service configured and ready",
                "details": {
                    "smtp_host": smtp_host_masked,
                    "smtp_port": settings.smtp_port,
                    "from_email": from_email_masked,  # Masked email
                    "use_tls": settings.smtp_use_tls,
                },
            }
        else:
            health_status["checks"]["email"] = {
                "status": "warning",
                "message": "Email service not configured (optional feature)",
                "details": {
                    "configured": False,
                    "note": "Email features will not be available",
                },
            }
    except Exception as e:
        health_status["checks"]["email"] = {
            "status": "warning",
            "message": f"Email service check skipped: {str(e)}",
        }

    # 5. Configuration Health Check
    try:
        config_issues = []
        config_warnings = []

        # Security checks
        if not settings.secret_key or settings.secret_key == "your-secret-key-here":
            config_issues.append("SECRET_KEY not properly configured - security risk!")

        if settings.debug:
            config_warnings.append(
                "Debug mode is enabled (not recommended for production)"
            )

        if not settings.allowed_origins or settings.allowed_origins == ["*"]:
            config_warnings.append(
                "CORS is configured to allow all origins (security concern)"
            )

        # Feature checks
        if not settings.database_url:
            config_issues.append("DATABASE_URL not configured")

        if config_issues:
            overall_healthy = False
            health_status["checks"]["configuration"] = {
                "status": "unhealthy",
                "message": "Critical configuration issues detected",
                "issues": config_issues,
                "warnings": config_warnings,
            }
        elif config_warnings:
            health_status["checks"]["configuration"] = {
                "status": "warning",
                "message": "Configuration warnings detected",
                "warnings": config_warnings,
            }
        else:
            health_status["checks"]["configuration"] = {
                "status": "healthy",
                "message": "Configuration validated successfully",
            }
    except Exception as e:
        health_status["checks"]["configuration"] = {
            "status": "warning",
            "message": f"Configuration check failed: {str(e)}",
        }

    # 6. Background Services Check
    try:
        from app.services.image_cleanup import is_cleanup_service_running

        cleanup_running = is_cleanup_service_running()

        health_status["checks"]["background_services"] = {
            "status": "healthy" if cleanup_running else "warning",
            "message": "Background services status",
            "details": {
                "image_cleanup": {
                    "running": cleanup_running,
                    "status": "active" if cleanup_running else "inactive",
                }
            },
        }
    except Exception as e:
        health_status["checks"]["background_services"] = {
            "status": "warning",
            "message": f"Background services check skipped: {str(e)}",
        }

    # Set overall status based on checks
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    elif any(
        check.get("status") == "degraded" for check in health_status["checks"].values()
    ):
        health_status["status"] = "degraded"
    elif any(
        check.get("status") == "warning" for check in health_status["checks"].values()
    ):
        health_status["status"] = "warning"

    # Count status types
    health_status["summary"] = {
        "total_checks": len(health_status["checks"]),
        "healthy": sum(
            1 for c in health_status["checks"].values() if c.get("status") == "healthy"
        ),
        "degraded": sum(
            1 for c in health_status["checks"].values() if c.get("status") == "degraded"
        ),
        "unhealthy": sum(
            1
            for c in health_status["checks"].values()
            if c.get("status") == "unhealthy"
        ),
        "warnings": sum(
            1 for c in health_status["checks"].values() if c.get("status") == "warning"
        ),
    }

    # Return appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 200  # Still operational but degraded
    else:
        status_code = 200

    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes/Docker liveness probe (PUBLIC)

    Returns 200 if the service is running.
    Use this for container orchestration liveness probes.
    No sensitive information is exposed.
    """
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/health/ready")
async def readiness_check(
    db: Session = Depends(get_db), redis_client: redis.Redis = Depends(get_redis)
):
    """
    Kubernetes/Docker readiness probe (PUBLIC)

    Returns 200 if the service is ready to accept traffic.
    Checks critical dependencies (database, cache) without exposing details.
    """
    ready = True
    checks = {}

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ready"
    except Exception:
        ready = False
        checks["database"] = "not ready"

    # Check redis (optional, don't fail on mock)
    try:
        redis_client.get("readiness_test")
        checks["cache"] = "ready"
    except Exception:
        checks["cache"] = "degraded"

    if ready:
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
        }
    else:
        return JSONResponse(
            content={
                "status": "not ready",
                "timestamp": datetime.now().isoformat(),
                "checks": checks,
            },
            status_code=503,
        )
