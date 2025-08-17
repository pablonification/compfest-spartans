from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from ..core.config import get_settings

client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection using Motor."""
    global client, mongo_db
    if client is None:
        settings = get_settings()
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongo_db = client[settings.MONGODB_DB_NAME]


async def close_mongo_connection() -> None:
    """Close MongoDB connection on shutdown."""
    global client
    if client is not None:
        client.close()


def get_database() -> AsyncIOMotorDatabase:
    """Get the MongoDB database instance."""
    if mongo_db is None:
        raise RuntimeError("MongoDB not initialized. Call connect_to_mongo() first.")
    return mongo_db
