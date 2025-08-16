"""Authentication router for SmartBin backend."""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import RedirectResponse

from ..services.service_factory import get_oauth_service, get_auth_service, get_user_service
from ..services.reward_service import get_user_stats
from ..domain.interfaces import OAuthService, AuthService, UserService
from ..auth.models import GoogleUserInfo
from ..models.user import User
from ..middleware.auth_middleware import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/google")
async def google_oauth_login() -> Any:
    """Initiate Google OAuth login flow."""
    try:
        oauth_service: OAuthService = get_oauth_service()
        auth_url, state = oauth_service.generate_authorization_url()
        
        logger.info("Generated OAuth authorization URL with state: %s", state)
        
        # Redirect to Google OAuth
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error("Failed to generate OAuth URL: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth login"
        )


@router.get("/google/callback")
async def google_oauth_callback(code: str, state: str) -> Any:
    """Handle Google OAuth callback and create user session."""
    try:
        oauth_service: OAuthService = get_oauth_service()
        user_service: UserService = get_user_service()
        auth_service: AuthService = get_auth_service()
        
        # Exchange code for tokens
        oauth_tokens = await oauth_service.exchange_code_for_tokens(code, state)
        
        # Get user info from Google
        google_user_info = await oauth_service.get_user_info(oauth_tokens.access_token)
        
        # Get or create user
        user = await user_service.get_or_create_user_from_oauth(google_user_info)
        
        # Update last login
        await user_service.update_user_last_login(str(user.id))
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token(str(user.id), user.email)
        refresh_token = auth_service.create_refresh_token(str(user.id), user.email)
        
        logger.info("User authenticated via OAuth: %s (ID: %s)", user.email, user.id)
        
        # In a real application, you might want to redirect to frontend with tokens
        # For now, return tokens in response (not recommended for production)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "points": user.points
            }
        }
        
    except Exception as e:
        logger.error("OAuth callback failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authentication failed"
        )


@router.post("/refresh")
async def refresh_token(request: Request) -> Any:
    """Refresh access token using refresh token."""
    try:
        # Extract refresh token from request
        refresh_token = request.headers.get("X-Refresh-Token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )
        
        auth_service: AuthService = get_auth_service()
        
        # Verify refresh token
        payload = auth_service.verify_token(refresh_token, "refresh")
        
        # Generate new access token
        new_access_token = auth_service.create_access_token(payload.sub, payload.email)
        
        logger.info("Token refreshed for user: %s", payload.sub)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(request: Request) -> Any:
    """Logout user (invalidate tokens on client side)."""
    # In a stateless JWT system, logout is handled client-side
    # Server can't invalidate JWT tokens, but client should remove them
    logger.info("User logout requested")
    
    return {
        "message": "Logout successful. Please remove tokens from client storage."
    }


@router.get("/profile", response_model=dict)
async def get_user_profile(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user profile and statistics."""
    try:
        # Get comprehensive user statistics
        user_stats = await get_user_stats(current_user)
        
        logger.info("Retrieved profile for user: %s", current_user.email)
        
        return user_stats
        
    except Exception as e:
        logger.error("Failed to get user profile for %s: %s", current_user.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.get("/stats", response_model=dict)
async def get_user_statistics(current_user: User = Depends(get_current_user)) -> Any:
    """Get detailed user statistics including scan history and rewards."""
    try:
        from ..services.service_factory import get_user_service
        
        # Get user service
        user_service: UserService = get_user_service()
        
        # Get fresh user data
        current_user_data = await user_service.get_user_by_id(str(current_user.id))
        if not current_user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user statistics
        user_stats = await get_user_stats(current_user_data)
        
        # Get scan history (basic info)
        scan_history = []
        if current_user_data.scan_ids:
            try:
                from ..db.mongo import mongo_db
                if mongo_db:
                    # Get recent scans for the user
                    scans = await mongo_db["scans"].find(
                        {"user_id": current_user_data.id}
                    ).sort("created_at", -1).limit(10).to_list(length=10)
                    
                    scan_history = [
                        {
                            "scan_id": str(scan["_id"]),
                            "brand": scan.get("brand"),
                            "points": scan.get("points", 0),
                            "valid": scan.get("valid", False),
                            "created_at": scan.get("created_at"),
                            "measurement": scan.get("measurement", {})
                        }
                        for scan in scans
                    ]
            except Exception as e:
                logger.warning("Failed to retrieve scan history: %s", e)
        
        # Compile comprehensive statistics
        comprehensive_stats = {
            **user_stats,
            "scan_history": scan_history,
            "total_scans": len(current_user_data.scan_ids),
            "successful_scans": len([s for s in scan_history if s.get("valid", False)]),
            "average_points_per_scan": (
                user_stats["total_rewards"] / len(scan_history) 
                if scan_history else 0
            ),
            "last_scan": scan_history[0] if scan_history else None
        }
        
        logger.info("Retrieved comprehensive statistics for user: %s", current_user.email)
        
        return comprehensive_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user statistics for %s: %s", current_user.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/leaderboard", response_model=dict)
async def get_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user leaderboard with current user's position."""
    try:
        from ..services.service_factory import get_user_service
        
        # Get user service
        user_service: UserService = get_user_service()
        
        # Get leaderboard
        leaderboard_users = await user_service.get_user_leaderboard(limit)
        
        # Find current user's position
        current_user_position = None
        for i, user in enumerate(leaderboard_users):
            if str(user.id) == str(current_user.id):
                current_user_position = i + 1
                break
        
        # Format leaderboard data
        leaderboard_data = [
            {
                "position": i + 1,
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name or "Anonymous",
                "points": user.points,
                "scan_count": len(user.scan_ids)
            }
            for i, user in enumerate(leaderboard_users)
        ]
        
        response = {
            "leaderboard": leaderboard_data,
            "current_user": {
                "position": current_user_position,
                "points": current_user.points,
                "scan_count": len(current_user.scan_ids)
            },
            "total_participants": len(leaderboard_data)
        }
        
        logger.info("Retrieved leaderboard for user: %s (position: %s)", 
                   current_user.email, current_user_position)
        
        return response
        
    except Exception as e:
        logger.error("Failed to get leaderboard: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve leaderboard"
        )


@router.get("/rewards", response_model=dict)
async def get_user_rewards(current_user: User = Depends(get_current_user)) -> Any:
    """Get user rewards and points information."""
    try:
        from ..services.reward_service import get_user_points
        
        # Get current points
        current_points = await get_user_points(current_user)
        
        # Get reward history (recent scans)
        reward_history = []
        try:
            from ..db.mongo import mongo_db
            if mongo_db:
                # Get recent scans with points for the user
                scans = await mongo_db["scans"].find(
                    {"user_id": current_user.id, "valid": True}
                ).sort("created_at", -1).limit(20).to_list(length=20)
                
                reward_history = [
                    {
                        "scan_id": str(scan["_id"]),
                        "brand": scan.get("brand"),
                        "points": scan.get("points", 0),
                        "created_at": scan.get("created_at"),
                        "measurement": scan.get("measurement", {})
                    }
                    for scan in scans
                ]
        except Exception as e:
            logger.warning("Failed to retrieve reward history: %s", e)
        
        # Calculate reward statistics
        total_rewards_earned = sum(scan["points"] for scan in reward_history)
        average_reward_per_scan = (
            total_rewards_earned / len(reward_history) 
            if reward_history else 0
        )
        
        # Get user's rank (approximate)
        try:
            from ..services.service_factory import get_user_service
            user_service: UserService = get_user_service()
            all_users = await user_service.get_user_leaderboard(1000)  # Get all users
            
            user_rank = None
            for i, user in enumerate(all_users):
                if str(user.id) == str(current_user.id):
                    user_rank = i + 1
                    break
        except Exception as e:
            logger.warning("Failed to calculate user rank: %s", e)
            user_rank = None
        
        response = {
            "current_points": current_points,
            "total_rewards_earned": total_rewards_earned,
            "total_scans": len(reward_history),
            "average_reward_per_scan": round(average_reward_per_scan, 2),
            "user_rank": user_rank,
            "reward_history": reward_history,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info("Retrieved rewards for user: %s (points: %d)", 
                   current_user.email, current_points)
        
        return response
        
    except Exception as e:
        logger.error("Failed to get user rewards for %s: %s", current_user.email, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user rewards"
        )


@router.get("/health")
async def auth_health_check() -> Any:
    """Health check for authentication service."""
    try:
        # Check if OAuth service is accessible
        oauth_service: OAuthService = get_oauth_service()
        auth_service: AuthService = get_auth_service()
        
        # Basic health checks
        health_status = {
            "status": "healthy",
            "service": "authentication",
            "oauth_provider": "google",
            "jwt_algorithm": auth_service.algorithm,
            "timestamp": "2024-12-19T00:00:00Z"  # This could be dynamic
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Authentication health check failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unhealthy"
        )
