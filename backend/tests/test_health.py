"""Unit and integration tests for backend foundation."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.config.settings import settings
from backend.app.database.mongodb import mongo_manager
from backend.app.database.redis import redis_manager


@pytest.mark.asyncio
async def test_configuration_validation():
    """Verify settings defaults and types."""
    assert settings.APP_NAME == "CrashSense AI Backend"
    assert settings.PORT == 8000
    assert settings.API_V1_PREFIX == "/api/v1"
    assert isinstance(settings.CORS_ORIGINS, list)


@pytest.mark.asyncio
async def test_root_health_endpoint():
    """Verify root GET /health responds with structured json."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["app_name"] == settings.APP_NAME
        assert "services" in data
        assert "mongodb" in data["services"]
        assert "redis" in data["services"]


@pytest.mark.asyncio
async def test_api_v1_health_endpoint():
    """Verify GET /api/v1/health returns health status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == settings.APP_VERSION
        assert data["environment"] == settings.APP_ENV


@pytest.mark.asyncio
async def test_system_info_endpoint():
    """Verify GET /api/v1/system/info returns metadata without exposing secrets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert data["api_prefix"] == "/api/v1"
        assert "services" in data
        # Ensure raw URI with passwords is not returned
        assert "mongodb+srv" not in str(data)


@pytest.mark.asyncio
async def test_database_health_handling():
    """Verify mongo_manager and redis_manager handle missing/unconnected cleanly."""
    mongo_health = await mongo_manager.check_health()
    assert "status" in mongo_health
    assert "configured" in mongo_health

    redis_health = await redis_manager.check_health()
    assert "status" in redis_health
    assert "configured" in redis_health

