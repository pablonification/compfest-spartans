from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status

from ..services.ws_manager import manager
from ..middleware.auth_middleware import get_optional_user
from ..models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/status")
async def websocket_status_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for authenticated connection")
) -> None:
    """WebSocket endpoint for real-time status updates.
    
    Supports both authenticated and anonymous connections.
    - With token: User-specific updates and personal messages
    - Without token: General broadcasts only
    """
    user_id: Optional[str] = None
    
    # Try to authenticate if token is provided
    if token:
        try:
            # Create a mock request context for token validation
            from fastapi import Request
            from ..services.service_factory import get_auth_service, get_user_service
            from ..auth.models import JWTPayload
            
            # Validate token
            auth_service = get_auth_service()
            payload: JWTPayload = auth_service.verify_token(token, "access")
            
            # Get user information
            user_service = get_user_service()
            user = await user_service.get_user_by_id(payload.sub)
            
            if user:
                user_id = str(user.id)
                logger.info("WebSocket authenticated for user: %s", user.email)
            else:
                logger.warning("WebSocket token valid but user not found: %s", payload.sub)
                
        except Exception as e:
            logger.warning("WebSocket authentication failed: %s", e)
            # Continue with anonymous connection
    
    # Connect to WebSocket manager
    await manager.connect(websocket, user_id)
    
    try:
        # Send connection confirmation
        if user_id:
            await websocket.send_json({
                "type": "connection_established",
                "data": {
                    "authenticated": True,
                    "user_id": user_id,
                    "message": "Connected with authentication"
                }
            })
        else:
            await websocket.send_json({
                "type": "connection_established",
                "data": {
                    "authenticated": False,
                    "message": "Connected anonymously"
                }
            })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive and process messages (keep connection open)
                message = await websocket.receive_text()
                
                # Handle ping/pong for connection health
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "stats":
                    # Send connection statistics
                    stats = {
                        "type": "connection_stats",
                        "data": {
                            "total_connections": manager.get_total_connection_count(),
                            "authenticated_users": manager.get_authenticated_user_count(),
                            "user_connections": manager.get_user_connection_count(user_id) if user_id else 0
                        }
                    }
                    await websocket.send_json(stats)
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/user/{user_id}")
async def websocket_user_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(..., description="JWT token required for user-specific WebSocket")
) -> None:
    """WebSocket endpoint for user-specific updates.
    
    Requires authentication and provides user-specific messages.
    """
    try:
        # Validate token and verify user access
        from ..services.service_factory import get_auth_service, get_user_service
        from ..auth.models import JWTPayload
        
        # Validate token
        auth_service = get_auth_service()
        payload: JWTPayload = auth_service.verify_token(token, "access")
        
        # Verify user access (users can only access their own WebSocket)
        if payload.sub != user_id:
            logger.warning("User %s attempted to access WebSocket for user %s", payload.sub, user_id)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Get user information
        user_service = get_user_service()
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            logger.warning("WebSocket user not found: %s", user_id)
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connect to WebSocket manager with user ID
        await manager.connect(websocket, user_id)
        
        logger.info("User-specific WebSocket connected for user: %s", user.email)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "user_connection_established",
            "data": {
                "user_id": user_id,
                "user_email": user.email,
                "message": "Connected to user-specific updates"
            }
        })
        
        # Keep connection alive
        while True:
            try:
                message = await websocket.receive_text()
                
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "user_stats":
                    # Send user-specific statistics
                    from ..services.reward_service import get_user_stats
                    user_stats = await get_user_stats(user)
                    stats_message = {
                        "type": "user_stats",
                        "data": user_stats
                    }
                    await websocket.send_json(stats_message)
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.debug("User WebSocket disconnected")
    except Exception as e:
        logger.error("User WebSocket error: %s", e)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        manager.disconnect(websocket)
