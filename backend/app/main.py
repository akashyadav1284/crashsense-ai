"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config.settings import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import global_exception_handler
from backend.app.database.mongodb import mongo_manager
from backend.app.database.redis import redis_manager
from backend.app.connectors.manager import connector_manager
from backend.app.api import api_v1_router
from backend.app.api.health import gather_health_state
from backend.app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager to connect/disconnect services gracefully."""
    logger.info("Starting up %s (version: %s, env: %s)...", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)
    await mongo_manager.connect()
    await redis_manager.connect()
    await connector_manager.initialize_database_indexes()
    try:
        yield
    finally:
        logger.info("Shutting down %s...", settings.APP_NAME)
        await redis_manager.disconnect()
        await mongo_manager.disconnect()
        logger.info("Graceful shutdown complete.")


def create_application() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="CRASHSENSE AI - Real-time predictive intelligence engine backend",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Global Exception Handler
    app.add_exception_handler(Exception, global_exception_handler)

    # CORS Middleware with strict allowlist
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root health endpoint
    @app.get("/health", response_model=HealthResponse, tags=["Health & System"])
    async def root_health() -> HealthResponse:
        """Root health check endpoint."""
        return await gather_health_state()

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
