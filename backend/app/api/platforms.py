"""Platforms API Router."""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.connectors.schemas.source import (
    PlatformConfig,
    PlatformCreateRequest,
    PlatformUpdateRequest,
)
from backend.app.connectors.schemas.connector import ConnectorHealthStatus
from backend.app.connectors.manager import connector_manager

router = APIRouter(prefix="/platforms", tags=["Platforms & Data Connectors"])


@router.get("", response_model=List[PlatformConfig])
async def list_platforms() -> List[PlatformConfig]:
    """Retrieve all configured platform data sources."""
    return await connector_manager.list_platforms()


@router.post("", response_model=PlatformConfig, status_code=status.HTTP_201_CREATED)
async def create_platform(req: PlatformCreateRequest) -> PlatformConfig:
    """Register a new platform data source."""
    existing = await connector_manager.get_platform(req.platform_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Platform with ID '{req.platform_id}' already exists."
        )

    config = PlatformConfig(
        platform_id=req.platform_id,
        platform_name=req.platform_name,
        integration_type=req.integration_type,
        provider_name=req.provider_name,
        configuration=req.configuration,
        authorization_status="NOT CONFIGURED"
    )
    return await connector_manager.save_platform(config)


@router.get("/{platform_id}", response_model=PlatformConfig)
async def get_platform(platform_id: str) -> PlatformConfig:
    """Get single platform configuration."""
    plat = await connector_manager.get_platform(platform_id)
    if not plat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found."
        )
    return plat


@router.patch("/{platform_id}", response_model=PlatformConfig)
async def update_platform(platform_id: str, req: PlatformUpdateRequest) -> PlatformConfig:
    """Update platform parameters."""
    plat = await connector_manager.get_platform(platform_id)
    if not plat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Platform '{platform_id}' not found.")

    if req.platform_name:
        plat.platform_name = req.platform_name
    if req.provider_name:
        plat.provider_name = req.provider_name
    if req.configuration is not None:
        plat.configuration.update(req.configuration)
    if req.authorization_status:
        plat.authorization_status = req.authorization_status
    if req.connection_status:
        plat.connection_status = req.connection_status

    return await connector_manager.save_platform(plat)


@router.get("/{platform_id}/health", response_model=ConnectorHealthStatus)
async def platform_health(platform_id: str) -> ConnectorHealthStatus:
    """Run health check against platform data source adapter."""
    plat = await connector_manager.get_platform(platform_id)
    if not plat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Platform '{platform_id}' not found.")

    connector = connector_manager.get_or_create_connector(platform_id)
    await connector.initialize()
    health = await connector.health_check()
    return health


@router.post("/{platform_id}/test-connection", response_model=Dict[str, Any])
async def test_platform_connection(platform_id: str) -> Dict[str, Any]:
    """Perform real handshake test without modifying state."""
    plat = await connector_manager.get_platform(platform_id)
    if not plat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Platform '{platform_id}' not found.")

    connector = connector_manager.get_or_create_connector(platform_id)
    await connector.initialize()
    health = await connector.health_check()
    return {
        "platform_id": platform_id,
        "connected": health.connected,
        "status": health.status,
        "latency_ms": health.latency_ms,
        "message": health.message
    }
