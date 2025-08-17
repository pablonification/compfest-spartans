from __future__ import annotations

import logging

from ..db.mongo import mongo_db
from ..models.user import User

logger = logging.getLogger(__name__)


async def add_points(email: str, points: int) -> int:
    """Add points to user; create user if not exists. Returns new total points."""
    if mongo_db is None:
        logger.warning("MongoDB not initialized; cannot add points")
        return 0

    collection = mongo_db["users"]
    result = await collection.find_one_and_update(
        {"email": email},
        {"$inc": {"points": points}},
        upsert=True,
        return_document=True,
    )
    # find_one_and_update may return None when upsert=True, driver specifics; ensure retrieval
    if result is None:
        result = await collection.find_one({"email": email})
    return int(result.get("points", 0))
