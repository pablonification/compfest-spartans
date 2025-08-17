from __future__ import annotations

import logging
import json
from typing import Set, Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            
            # Store connection info
            client_info = {
                'connected_at': datetime.now().isoformat(),
                'client_ip': websocket.client.host if websocket.client else 'unknown',
                'client_port': websocket.client.port if websocket.client else 'unknown'
            }
            self.connection_info[websocket] = client_info
            
            logger.info("WebSocket client connected from %s:%s (%d total connections)", 
                       client_info['client_ip'], client_info['client_port'], len(self.active_connections))
            
            # Send welcome message
            await websocket.send_json({
                'type': 'connection_status',
                'status': 'connected',
                'message': 'WebSocket connection established successfully',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error("Failed to accept WebSocket connection: %s", str(e))
            raise

    def disconnect(self, websocket: WebSocket) -> None:
        try:
            self.active_connections.discard(websocket)
            client_info = self.connection_info.pop(websocket, {})
            logger.info("WebSocket client disconnected from %s:%s (%d total connections)", 
                       client_info.get('client_ip', 'unknown'), 
                       client_info.get('client_port', 'unknown'), 
                       len(self.active_connections))
        except Exception as e:
            logger.error("Error during WebSocket disconnect: %s", str(e))

    async def broadcast(self, message: dict) -> None:
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to")
            return
            
        disconnected: Set[WebSocket] = set()
        message['timestamp'] = datetime.now().isoformat()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.debug("Message broadcasted to client %s:%s", 
                           self.connection_info.get(connection, {}).get('client_ip', 'unknown'),
                           self.connection_info.get(connection, {}).get('client_port', 'unknown'))
            except WebSocketDisconnect:
                logger.debug("WebSocket disconnected during broadcast")
                disconnected.add(connection)
            except Exception as e:
                logger.error("Error broadcasting message: %s", str(e))
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> bool:
        """Send a message to a specific WebSocket connection"""
        try:
            if websocket in self.active_connections:
                message['timestamp'] = datetime.now().isoformat()
                await websocket.send_json(message)
                logger.debug("Personal message sent to client %s:%s", 
                           self.connection_info.get(websocket, {}).get('client_ip', 'unknown'),
                           self.connection_info.get(websocket, {}).get('client_port', 'unknown'))
                return True
            else:
                logger.warning("Attempted to send message to inactive WebSocket connection")
                return False
        except Exception as e:
            logger.error("Error sending personal message: %s", str(e))
            return False

    def get_connection_count(self) -> int:
        """Get the current number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about all active connections"""
        return {
            'total_connections': len(self.active_connections),
            'connections': [
                {
                    'client_ip': info.get('client_ip', 'unknown'),
                    'client_port': info.get('client_port', 'unknown'),
                    'connected_at': info.get('connected_at', 'unknown')
                }
                for info in self.connection_info.values()
            ]
        }


# Global singleton manager
manager = ConnectionManager()
