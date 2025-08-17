from __future__ import annotations

import logging

from ..db.mongo import mongo_db
from ..models.user import User
from .notification_service import get_notification_service

logger = logging.getLogger(__name__)


async def add_points(email: str, points: int, bottle_count: int = 1) -> int:
    """Add points to user; create user if not exists. Returns new total points."""
    if mongo_db is None:
        logger.warning("MongoDB not initialized; cannot add points")
        return 0

    collection = mongo_db["users"]
    result = await collection.find_one_and_update(
        {"email": email},
        {"$inc": {"points": points}},
        return_document=True,
    )
    # find_one_and_update may return None when upsert=True, driver specifics; ensure retrieval
    if result is None:
        result = await collection.find_one({"email": email})
    
    # Create reward notification
        try:
            user_id = result.get("_id")
            if user_id:
                notification_service = get_notification_service()
                await notification_service.create_reward_notification(
                    user_id=user_id,
                    points=points,
                    bottle_count=bottle_count
                )
        except Exception as e:
            logger.warning(f"Failed to create reward notification: {e}")
    
    return int(result.get("points", 0))
