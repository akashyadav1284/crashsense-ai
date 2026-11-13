"""MongoDB connection manager using Motor (async PyMongo driver)."""
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.app.config.settings import settings
from backend.app.core.logging import logger


class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """Establish asynchronous connection to MongoDB Atlas."""
        if not settings.MONGODB_URI:
            logger.warning("MONGODB_URI is not configured. Database will operate in unconfigured mode.")
            return

        try:
            logger.info("Initializing connection to MongoDB...")
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000
            )
            cls.database = cls.client[settings.MONGODB_DATABASE]
            # Verify connectivity
            await cls.client.admin.command("ping")
            logger.info("Successfully connected and pinged MongoDB database: %s", settings.MONGODB_DATABASE)
        except Exception as exc:
            logger.error("Failed to connect to MongoDB: %s", str(exc))
            # Keep client references safe without crashing startup
            cls.client = None
            cls.database = None

    @classmethod
    async def disconnect(cls) -> None:
        """Gracefully close the MongoDB client connection."""
        if cls.client is not None:
            logger.info("Closing MongoDB connection pool...")
            cls.client.close()
            cls.client = None
            cls.database = None
            logger.info("MongoDB connection closed.")

    @classmethod
    async def check_health(cls) -> Dict[str, Any]:
        """Verify live MongoDB connection and return health metadata."""
        if not settings.MONGODB_URI:
            return {
                "status": "unconfigured",
                "configured": False,
                "database": settings.MONGODB_DATABASE,
                "message": "MONGODB_URI environment variable is missing"
            }

        if cls.client is None:
            return {
                "status": "disconnected",
                "configured": True,
                "database": settings.MONGODB_DATABASE,
                "message": "MongoDB client is not connected"
            }

        try:
            await cls.client.admin.command("ping")
            return {
                "status": "connected",
                "configured": True,
                "database": settings.MONGODB_DATABASE,
                "message": "MongoDB ping succeeded"
            }
        except Exception as exc:
            return {
                "status": "error",
                "configured": True,
                "database": settings.MONGODB_DATABASE,
                "message": str(exc)
            }


mongo_manager = MongoDBManager

