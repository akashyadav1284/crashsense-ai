"""Redis connection manager."""
from typing import Optional, Dict, Any
import redis.asyncio as aioredis
from backend.app.config.settings import settings
from backend.app.core.logging import logger


class RedisManager:
    client: Optional[aioredis.Redis] = None

    @classmethod
    async def connect(cls) -> None:
        """Establish asynchronous connection to Redis."""
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL is not configured. Redis will operate in unconfigured mode.")
            return

        try:
            logger.info("Initializing connection to Redis at %s...", settings.REDIS_URL)
            cls.client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0
            )
            # Verify connectivity
            await cls.client.ping()
            logger.info("Successfully connected and pinged Redis.")
        except Exception as exc:
            logger.error("Failed to connect to Redis: %s", str(exc))
            # Safe fallback
            if cls.client:
                await cls.client.aclose()
            cls.client = None

    @classmethod
    async def disconnect(cls) -> None:
        """Gracefully close the Redis client connection."""
        if cls.client is not None:
            logger.info("Closing Redis connection...")
            await cls.client.aclose()
            cls.client = None
            logger.info("Redis connection closed.")

    @classmethod
    async def check_health(cls) -> Dict[str, Any]:
        """Verify live Redis connection and return health metadata."""
        if not settings.REDIS_URL:
            return {
                "status": "unconfigured",
                "configured": False,
                "message": "REDIS_URL environment variable is missing"
            }

        if cls.client is None:
            return {
                "status": "disconnected",
                "configured": True,
                "message": "Redis client is not connected"
            }

        try:
            ping_res = await cls.client.ping()
            if ping_res:
                return {
                    "status": "connected",
                    "configured": True,
                    "message": "Redis ping succeeded"
                }
            return {
                "status": "disconnected",
                "configured": True,
                "message": "Redis did not respond with PONG"
            }
        except Exception as exc:
            return {
                "status": "error",
                "configured": True,
                "message": str(exc)
            }


redis_manager = RedisManager

