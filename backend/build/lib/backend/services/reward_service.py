from __future__ import annotations

import logging
from typing import Optional

from ..domain.interfaces import UserService
from ..services.service_factory import get_user_service
from ..models.user import User

logger = logging.getLogger(__name__)


async def add_points(user: User, points: int) -> int:
    """Add points to authenticated user. Returns new total points.
    
    Args:
        user: Authenticated user instance
        points: Points to add
        
    Returns:
        int: New total points after addition
    """
    try:
        # Get user service through factory
        user_service: UserService = get_user_service()
        
        # Update user points
        updated_user = await user_service.add_points(user.id, points)
        
        logger.info("Added %d points to user %s. New total: %d", 
                   points, user.email, updated_user.points)
        
        return updated_user.points
        
    except Exception as e:
        logger.error("Failed to add points for user %s: %s", user.email, e)
        # Return current points if update fails
        return user.points


async def get_user_points(user: User) -> int:
    """Get current points for authenticated user.
    
    Args:
        user: Authenticated user instance
        
    Returns:
        int: Current user points
    """
    try:
        # Get user service through factory
        user_service: UserService = get_user_service()
        
        # Get fresh user data
        current_user = await user_service.get_user_by_id(user.id)
        if current_user:
            return current_user.points
        
        return user.points
        
    except Exception as e:
        logger.error("Failed to get points for user %s: %s", user.email, e)
        return user.points


async def get_user_stats(user: User) -> dict:
    """Get comprehensive statistics for authenticated user.
    
    Args:
        user: Authenticated user instance
        
    Returns:
        dict: User statistics including points, scan count, etc.
    """
    try:
        # Get user service through factory
        user_service: UserService = get_user_service()
        
        # Get fresh user data with statistics
        current_user = await user_service.get_user_by_id(user.id)
        if not current_user:
            return {
                "email": user.email,
                "points": user.points,
                "scan_count": 0,
                "total_rewards": 0
            }
        
        # Calculate statistics (this could be enhanced with scan repository)
        stats = {
            "email": current_user.email,
            "points": current_user.points,
            "scan_count": len(current_user.scan_ids),
            "total_rewards": current_user.points,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get stats for user %s: %s", user.email, e)
        return {
            "email": user.email,
            "points": user.points,
            "scan_count": 0,
            "total_rewards": 0,
            "error": "Failed to retrieve statistics"
        }
