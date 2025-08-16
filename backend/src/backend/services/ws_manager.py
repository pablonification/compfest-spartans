from __future__ import annotations

import logging
from typing import Set, Dict, Optional
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> set of connections
        self.connection_users: Dict[WebSocket, str] = {}  # connection -> user_id

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> None:
        """Connect a WebSocket client, optionally associated with a user.
        
        Args:
            websocket: WebSocket connection
            user_id: Optional user ID for authenticated connections
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if user_id:
            # Track user-specific connection
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
            self.connection_users[websocket] = user_id
            logger.debug("WS client connected for user %s (%d total connections)", 
                        user_id, len(self.active_connections))
        else:
            # Anonymous connection
            logger.debug("WS client connected anonymously (%d total connections)", 
                        len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a WebSocket client and clean up user associations."""
        self.active_connections.discard(websocket)
        
        # Clean up user associations
        user_id = self.connection_users.pop(websocket, None)
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.debug("WS client disconnected (%d total connections)", len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        disconnected: Set[WebSocket] = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_to_user(self, user_id: str, message: dict) -> None:
        """Broadcast message to all connections of a specific user.
        
        Args:
            user_id: User ID to broadcast to
            message: Message to send
        """
        if user_id not in self.user_connections:
            logger.debug("No active connections for user %s", user_id)
            return
        
        disconnected: Set[WebSocket] = set()
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message to send
        """
        try:
            await websocket.send_json(message)
        except WebSocketDisconnect:
            self.disconnect(websocket)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get the number of active connections for a user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            int: Number of active connections
        """
        return len(self.user_connections.get(user_id, set()))

    def get_total_connection_count(self) -> int:
        """Get the total number of active connections.
        
        Returns:
            int: Total number of active connections
        """
        return len(self.active_connections)

    def get_authenticated_user_count(self) -> int:
        """Get the number of users with active connections.
        
        Returns:
            int: Number of authenticated users
        """
        return len(self.user_connections)

    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if user has active connections
        """
        return user_id in self.user_connections and bool(self.user_connections[user_id])


# Global singleton manager
manager = ConnectionManager()
