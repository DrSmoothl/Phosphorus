"""MongoDB database connection and utilities."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from .config import settings
from .logger import get_logger

logger = get_logger()


class DatabaseManager:
    """MongoDB database manager."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Connect to MongoDB."""
        if self._client is not None:
            return

        try:
            self._client = AsyncIOMotorClient(settings.mongodb_url)
            # Test connection
            await self._client.admin.command("ping")
            self._database = self._client[settings.mongodb_database]
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Disconnected from MongoDB")

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get client instance."""
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client


# Global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if db_manager._database is None:
        await db_manager.connect()
    return db_manager.database
