"""Health and system inspection API routes."""
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.config.settings import settings
from backend.app.database.mongodb import mongo_manager
from backend.app.database.redis import redis_manager
from backend.app.schemas.health import HealthResponse, SystemInfoResponse

router = APIRouter(tags=["Health & System"])


async def gather_health_state() -> HealthResponse:
    mongo_health = await mongo_manager.check_health()
    redis_health = await redis_manager.check_health()

    # Determine aggregated status
    all_connected = (
        (not settings.MONGODB_URI or mongo_health["status"] == "connected") and
        (not settings.REDIS_URL or redis_health["status"] == "connected")
    )
    overall_status = "healthy" if all_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        services={
            "mongodb": mongo_health,
            "redis": redis_health,
        }
    )


@router.get("/health", response_model=HealthResponse)
async def api_health() -> HealthResponse:
    """Detailed health check for API v1."""
    return await gather_health_state()


@router.get("/system/info", response_model=SystemInfoResponse)
async def system_info() -> SystemInfoResponse:
    """System information without exposing sensitive credentials."""
    mongo_health = await mongo_manager.check_health()
    redis_health = await redis_manager.check_health()

    return SystemInfoResponse(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        api_prefix=settings.API_V1_PREFIX,
        services={
            "mongodb": {
                "configured": bool(settings.MONGODB_URI),
                "status": mongo_health["status"],
                "database": settings.MONGODB_DATABASE
            },
            "redis": {
                "configured": bool(settings.REDIS_URL),
                "status": redis_health["status"]
            }
        }
    )

