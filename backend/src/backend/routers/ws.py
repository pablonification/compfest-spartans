from __future__ import annotations

import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

from ..services.ws_manager import manager  # singleton

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time status updates and scan results"""
    try:
        # Accept the connection
        await manager.connect(websocket)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                if data:
                    try:
                        message = json.loads(data)
                        logger.debug("Received WebSocket message: %s", message)
                        
                        # Handle different message types
                        if message.get('type') == 'ping':
                            # Respond to ping with pong
                            await manager.send_personal_message({
                                'type': 'pong',
                                'timestamp': message.get('timestamp')
                            }, websocket)
                            
                        elif message.get('type') == 'scan_request':
                            # Handle scan request
                            await manager.send_personal_message({
                                'type': 'scan_status',
                                'status': 'processing',
                                'message': 'Scan request received'
                            }, websocket)
                            
                        else:
                            # Echo back unknown message types
                            await manager.send_personal_message({
                                'type': 'echo',
                                'data': message,
                                'message': 'Message received'
                            }, websocket)
                            
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON from WebSocket client")
                        await manager.send_personal_message({
                            'type': 'error',
                            'message': 'Invalid JSON format'
                        }, websocket)
                        
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
                
    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Ensure cleanup happens
        manager.disconnect(websocket)


@router.get("/ws/health")
async def websocket_health_check():
    """Health check endpoint for WebSocket service"""
    try:
        connection_info = manager.get_connection_info()
        return JSONResponse({
            'status': 'healthy',
            'websocket_service': 'running',
            'active_connections': connection_info['total_connections'],
            'connections': connection_info['connections']
        })
    except Exception as e:
        logger.error("WebSocket health check failed: %s", str(e))
        raise HTTPException(status_code=500, detail="WebSocket service unhealthy")


@router.post("/ws/broadcast")
async def broadcast_message(message: dict):
    """Admin endpoint to broadcast messages to all connected WebSocket clients"""
    try:
        await manager.broadcast(message)
        return JSONResponse({
            'status': 'success',
            'message': f'Message broadcasted to {manager.get_connection_count()} clients'
        })
    except Exception as e:
        logger.error("Failed to broadcast message: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to broadcast message")
