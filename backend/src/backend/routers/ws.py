from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import logging
from typing import Optional

from ..services.ws_manager import get_connection_manager, start_websocket_manager, stop_websocket_manager
from ..models.user import User
import jwt
from ..core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

settings = get_settings()

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload (for WebSocket use)"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


async def get_current_user_from_token(token: str) -> Optional[User]:
    """Get current user from JWT token."""
    try:
        from bson import ObjectId
        from ..db.mongo import ensure_connection
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return None
        
        # Get user from database
        db = await ensure_connection()
        users_collection = db.users
        
        user_id = ObjectId(payload["sub"])
        user = await users_collection.find_one({"_id": user_id})
        
        if user:
            return User(**user)
        return None
        
    except Exception as e:
        logger.error(f"Error getting user from token: {e}")
        return None


@router.websocket("/ws/notifications/{user_id}")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: str
):
    """WebSocket endpoint for real-time notifications."""
    connection_manager = await get_connection_manager()
    
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "status": "connecting",
            "message": "Establishing connection...",
            "timestamp": "2024-01-01T00:00:00Z"
        }))
        
        # Wait for authentication token from client
        try:
            # Wait for the first message which should contain the token
            data = await websocket.receive_text()
            logger.info(f"Received initial message from user {user_id}: {data}")
            
            try:
                auth_data = json.loads(data)
                token = auth_data.get("token")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from user {user_id}: {data}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                await websocket.close(code=1008, reason="Invalid JSON")
                return
            
            if not token:
                logger.warning(f"No token provided by user {user_id}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Authentication token required",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                await websocket.close(code=1008, reason="Authentication required")
                return
            
            # Verify token and get user
            user = await get_current_user_from_token(token)
            if not user:
                logger.warning(f"Invalid token for user {user_id}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid authentication token",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                await websocket.close(code=1008, reason="Invalid token")
                return
            
            if str(user.id) != user_id:
                logger.warning(f"User ID mismatch: token user {user.id} vs path user {user_id}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "User ID mismatch",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
                await websocket.close(code=1008, reason="User ID mismatch")
                return
            
            # Authentication successful, connect to manager
            await connection_manager.connect(websocket, user_id)
            
            # Send success message
            await websocket.send_text(json.dumps({
                "type": "connection_status",
                "status": "connected",
                "message": f"Connected as user {user.email}",
                "user_id": user_id,
                "timestamp": "2024-01-01T00:00:00Z"
            }))
            
            logger.info(f"User {user_id} ({user.email}) authenticated and connected to WebSocket")
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    
                    try:
                        message = json.loads(data)
                        message_type = message.get("type")
                        
                        if message_type == "ping":
                            # Respond to ping
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "timestamp": "2024-01-01T00:00:00Z"
                            }))
                        elif message_type == "get_status":
                            # Send connection status
                            await websocket.send_text(json.dumps({
                                "type": "status_response",
                                "data": {
                                    "user_id": user_id,
                                    "connection_count": connection_manager.get_connection_count(),
                                    "user_count": connection_manager.get_user_count()
                                },
                                "timestamp": "2024-01-01T00:00:00Z"
                            }))
                        else:
                            # Echo back unknown message types
                            await websocket.send_text(json.dumps({
                                "type": "echo",
                                "data": message,
                                "timestamp": "2024-01-01T00:00:00Z"
                            }))
                            
                    except json.JSONDecodeError:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format",
                            "timestamp": "2024-01-01T00:00:00Z"
                        }))
                        
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected for user {user_id}")
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message for user {user_id}: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Internal server error: {str(e)}",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }))
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected during authentication for user {user_id}")
        except Exception as e:
            logger.error(f"Error during WebSocket authentication for user {user_id}: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Authentication error: {str(e)}",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
            except:
                pass
            await websocket.close(code=1011, reason="Internal error")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint for user {user_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
    finally:
        # Always disconnect from manager
        connection_manager.disconnect(websocket)


@router.websocket("/ws/public")
async def websocket_public_endpoint(websocket: WebSocket):
    """Public WebSocket endpoint for system-wide broadcasts."""
    connection_manager = await get_connection_manager()
    
    try:
        await websocket.accept()
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_status",
            "status": "connected",
            "message": "Connected to public notification channel",
            "timestamp": "2024-01-01T00:00:00Z"
        }))
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": "2024-01-01T00:00:00Z"
                        }))
                    else:
                        # Echo back message
                        await websocket.send_text(json.dumps({
                            "type": "echo",
                            "data": message,
                            "timestamp": "2024-01-01T00:00:00Z"
                        }))
                        
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in public WebSocket: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("Public WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in public WebSocket endpoint: {e}")
    finally:
        # Note: Public connections don't need to be tracked in the manager
        pass


@router.get("/ws/status")
async def get_websocket_status():
    """Get WebSocket connection status."""
    connection_manager = await get_connection_manager()
    
    return {
        "total_connections": connection_manager.get_connection_count(),
        "total_users": connection_manager.get_user_count(),
        "status": "active"
    }


@router.post("/ws/start")
async def start_websocket_manager_endpoint():
    """Start the WebSocket manager (admin only)."""
    try:
        await start_websocket_manager()
        return {"message": "WebSocket manager started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start WebSocket manager: {str(e)}")


@router.post("/ws/stop")
async def stop_websocket_manager_endpoint():
    """Stop the WebSocket manager (admin only)."""
    try:
        await stop_websocket_manager()
        return {"message": "WebSocket manager stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop WebSocket manager: {str(e)}")


@router.post("/ws/broadcast")
async def broadcast_message_endpoint(message: dict):
    """Broadcast a message to all connected WebSocket clients (admin only)."""
    try:
        connection_manager = await get_connection_manager()
        await connection_manager.broadcast_notification(message)
        return {"message": "Message broadcasted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to broadcast message: {str(e)}")


@router.post("/ws/send/{user_id}")
async def send_message_to_user_endpoint(user_id: str, message: dict):
    """Send a message to a specific user (admin only)."""
    try:
        connection_manager = await get_connection_manager()
        await connection_manager.send_notification_to_user(user_id, message)
        return {"message": f"Message sent to user {user_id} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
