from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi
from ..core.config import get_settings
import asyncio
import logging
import random

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None
mongo_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global client, mongo_db
    if client is not None:
        return
    settings = get_settings()
    client = AsyncIOMotorClient(
        settings.MONGODB_URI,               # mongodb+srv://.../?retryWrites=true&w=majority&appName=SmartBin
        server_api=ServerApi('1'),
        maxPoolSize=10,
        minPoolSize=1,
        maxIdleTimeMS=30000,
        connectTimeoutMS=10000,
        serverSelectionTimeoutMS=10000,
        heartbeatFrequencyMS=10000,
    )
    await client.admin.command('ping')
    mongo_db = client[settings.MONGODB_DB_NAME]
    logger.info("✅ MongoDB connected. DB=%s", settings.MONGODB_DB_NAME)


async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
        client = None


async def ensure_connection(max_retries: int = 3) -> AsyncIOMotorDatabase:
    global mongo_db, client
    for attempt in range(1, max_retries + 1):
        try:
            if client is None or mongo_db is None:
                await connect_to_mongo()
            await client.admin.command('ping')
            return mongo_db
        except Exception as e:
            wait = min(2 ** attempt, 8) + random.random()
            logger.warning(
                "Mongo ping failed (attempt %d/%d): %s. Retrying in %.1fs",
                attempt, max_retries, e, wait
            )
            await asyncio.sleep(wait)
            client = None
            mongo_db = None
    raise RuntimeError("MongoDB connection unavailable after retries")


def get_database() -> AsyncIOMotorDatabase:
    if mongo_db is None:
        raise RuntimeError("MongoDB not initialized. Call connect_to_mongo() first.")
    return mongo_db
