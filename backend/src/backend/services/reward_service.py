from __future__ import annotations

import logging

from ..db.mongo import ensure_connection
from ..models.user import User
from .notification_service import get_notification_service

logger = logging.getLogger(__name__)


async def add_points(email: str, points: int, bottle_count: int = 1) -> int:
    """Add points to user; create user if not exists. Returns new total points."""
    logger.info(f"add_points called: email={email}, points={points}, bottle_count={bottle_count}")
    try:
        db = await ensure_connection()
        collection = db["users"]
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return 0

    logger.info(f"Finding user with email: {email}")
    
    # First, let's see what the user document looks like before update
    user_before = await collection.find_one({"email": email})
    logger.info(f"User before update: {user_before}")
    
    result = await collection.find_one_and_update(
        {"email": email},
        {"$inc": {"points": points}},
        return_document=True,
        upsert=True,
    )
    logger.info(f"find_one_and_update result: {result}")
    
    # find_one_and_update may return None when upsert=True, driver specifics; ensure retrieval
    if result is None:
        logger.warning("find_one_and_update returned None, trying to find user again")
        result = await collection.find_one({"email": email})
        logger.info(f"User after fallback find: {result}")
    
    final_points = int(result.get("points", 0)) if result else 0
    logger.info(f"Final points returned: {final_points}")
    
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
    
    return final_points
