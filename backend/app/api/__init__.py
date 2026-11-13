"""API v1 router aggregator."""
from fastapi import APIRouter
from backend.app.api.health import router as health_router
from backend.app.api.platforms import router as platforms_router
from backend.app.api.imports import router as imports_router
from backend.app.api.rounds import router as rounds_router
from backend.app.api.websocket import router as ws_router
from backend.app.api.datasets import router as datasets_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.ml import router as ml_router
from backend.app.api.realtime import router as realtime_router
from backend.app.api.simulation import router as simulation_router, risk_router, mc_router
from backend.app.api.notifications import (
    router_notifications,
    router_alerts,
    router_users,
    router_admin,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(platforms_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(rounds_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(ml_router)
api_v1_router.include_router(realtime_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(mc_router)
api_v1_router.include_router(router_notifications)
api_v1_router.include_router(router_alerts)
api_v1_router.include_router(router_users)
api_v1_router.include_router(router_admin)
api_v1_router.include_router(ws_router)
