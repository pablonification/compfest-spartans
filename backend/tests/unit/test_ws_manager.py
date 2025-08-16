"""Unit tests for WebSocket manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, WebSocketDisconnect

from src.backend.services.ws_manager import ConnectionManager


class TestConnectionManager:
    """Test cases for WebSocket connection manager."""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing."""
        websocket = AsyncMock(spec=WebSocket)
        websocket.send_json = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket

    @pytest.fixture
    def connection_manager(self):
        """Create a connection manager instance for testing."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_anonymous(self, connection_manager, mock_websocket):
        """Test connecting an anonymous WebSocket."""
        await connection_manager.connect(mock_websocket)
        
        assert mock_websocket in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 1
        assert len(connection_manager.user_connections) == 0

    @pytest.mark.asyncio
    async def test_connect_authenticated(self, connection_manager, mock_websocket):
        """Test connecting an authenticated WebSocket."""
        user_id = "test_user_123"
        await connection_manager.connect(mock_websocket, user_id)
        
        assert mock_websocket in connection_manager.active_connections
        assert user_id in connection_manager.user_connections
        assert mock_websocket in connection_manager.user_connections[user_id]
        assert connection_manager.connection_users[mock_websocket] == user_id

    @pytest.mark.asyncio
    async def test_connect_multiple_users(self, connection_manager):
        """Test connecting multiple users."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        await connection_manager.connect(websocket1, "user1")
        await connection_manager.connect(websocket2, "user2")
        
        assert len(connection_manager.active_connections) == 2
        assert len(connection_manager.user_connections) == 2
        assert "user1" in connection_manager.user_connections
        assert "user2" in connection_manager.user_connections

    @pytest.mark.asyncio
    async def test_connect_same_user_multiple_connections(self, connection_manager):
        """Test connecting the same user with multiple WebSocket connections."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        await connection_manager.connect(websocket1, "user1")
        await connection_manager.connect(websocket2, "user1")
        
        assert len(connection_manager.active_connections) == 2
        assert len(connection_manager.user_connections) == 1
        assert len(connection_manager.user_connections["user1"]) == 2

    @pytest.mark.asyncio
    async def test_disconnect_anonymous(self, connection_manager, mock_websocket):
        """Test disconnecting an anonymous WebSocket."""
        await connection_manager.connect(mock_websocket)
        connection_manager.disconnect(mock_websocket)
        
        assert mock_websocket not in connection_manager.active_connections
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect_authenticated(self, connection_manager, mock_websocket):
        """Test disconnecting an authenticated WebSocket."""
        user_id = "test_user_123"
        await connection_manager.connect(mock_websocket, user_id)
        connection_manager.disconnect(mock_websocket)
        
        assert mock_websocket not in connection_manager.active_connections
        assert user_id not in connection_manager.user_connections
        assert mock_websocket not in connection_manager.connection_users

    @pytest.mark.asyncio
    async def test_disconnect_removes_empty_user_connections(self, connection_manager):
        """Test that empty user connections are removed on disconnect."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        await connection_manager.connect(websocket1, "user1")
        await connection_manager.connect(websocket2, "user1")
        
        # Disconnect first websocket
        connection_manager.disconnect(websocket1)
        assert "user1" in connection_manager.user_connections
        assert len(connection_manager.user_connections["user1"]) == 1
        
        # Disconnect second websocket
        connection_manager.disconnect(websocket2)
        assert "user1" not in connection_manager.user_connections

    @pytest.mark.asyncio
    async def test_broadcast_success(self, connection_manager):
        """Test successful broadcast to all connections."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        await connection_manager.connect(websocket1)
        await connection_manager.connect(websocket2)
        
        message = {"type": "test", "data": "test_message"}
        await connection_manager.broadcast(message)
        
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_with_disconnect_handling(self, connection_manager):
        """Test broadcast handling when connections disconnect."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        # Make websocket2 raise WebSocketDisconnect
        websocket2.send_json.side_effect = WebSocketDisconnect()
        
        await connection_manager.connect(websocket1)
        await connection_manager.connect(websocket2)
        
        message = {"type": "test", "data": "test_message"}
        await connection_manager.broadcast(message)
        
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
        
        # websocket2 should be removed
        assert websocket2 not in connection_manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_to_user_success(self, connection_manager):
        """Test successful broadcast to specific user."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        await connection_manager.connect(websocket1, "user1")
        await connection_manager.connect(websocket2, "user2")
        
        message = {"type": "test", "data": "user1_message"}
        await connection_manager.broadcast_to_user("user1", message)
        
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_user_not_connected(self, connection_manager):
        """Test broadcast to user who is not connected."""
        message = {"type": "test", "data": "test_message"}
        
        # Should not raise any exception
        await connection_manager.broadcast_to_user("nonexistent_user", message)

    @pytest.mark.asyncio
    async def test_broadcast_to_user_with_disconnect_handling(self, connection_manager):
        """Test broadcast to user with disconnect handling."""
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        
        # Make websocket2 raise WebSocketDisconnect
        websocket2.send_json.side_effect = WebSocketDisconnect()
        
        await connection_manager.connect(websocket1, "user1")
        await connection_manager.connect(websocket2, "user1")
        
        message = {"type": "test", "data": "user1_message"}
        await connection_manager.broadcast_to_user("user1", message)
        
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)
        
        # websocket2 should be removed
        assert websocket2 not in connection_manager.active_connections
        assert websocket2 not in connection_manager.user_connections["user1"]

    @pytest.mark.asyncio
    async def test_send_personal_message_success(self, connection_manager, mock_websocket):
        """Test successful personal message sending."""
        await connection_manager.connect(mock_websocket)
        
        message = {"type": "personal", "data": "personal_message"}
        await connection_manager.send_personal_message(mock_websocket, message)
        
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_with_disconnect(self, connection_manager, mock_websocket):
        """Test personal message sending when connection disconnects."""
        await connection_manager.connect(mock_websocket)
        
        # Make websocket raise WebSocketDisconnect
        mock_websocket.send_json.side_effect = WebSocketDisconnect()
        
        message = {"type": "personal", "data": "personal_message"}
        await connection_manager.send_personal_message(mock_websocket, message)
        
        # websocket should be removed
        assert mock_websocket not in connection_manager.active_connections

    def test_get_user_connection_count(self, connection_manager):
        """Test getting user connection count."""
        assert connection_manager.get_user_connection_count("user1") == 0
        
        # Add a connection
        websocket = AsyncMock(spec=WebSocket)
        connection_manager.user_connections["user1"] = {websocket}
        
        assert connection_manager.get_user_connection_count("user1") == 1

    def test_get_total_connection_count(self, connection_manager):
        """Test getting total connection count."""
        assert connection_manager.get_total_connection_count() == 0
        
        # Add connections
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)
        connection_manager.active_connections.add(websocket1)
        connection_manager.active_connections.add(websocket2)
        
        assert connection_manager.get_total_connection_count() == 2

    def test_get_authenticated_user_count(self, connection_manager):
        """Test getting authenticated user count."""
        assert connection_manager.get_authenticated_user_count() == 0
        
        # Add user connections
        connection_manager.user_connections["user1"] = set()
        connection_manager.user_connections["user2"] = set()
        
        assert connection_manager.get_authenticated_user_count() == 2

    def test_is_user_connected(self, connection_manager):
        """Test checking if user is connected."""
        assert not connection_manager.is_user_connected("user1")
        
        # Add user connection
        connection_manager.user_connections["user1"] = {AsyncMock(spec=WebSocket)}
        
        assert connection_manager.is_user_connected("user1")
        
        # Test with empty connection set
        connection_manager.user_connections["user1"] = set()
        assert not connection_manager.is_user_connected("user1")

    @pytest.mark.asyncio
    async def test_connection_manager_singleton(self):
        """Test that the global manager is a singleton."""
        from src.backend.services.ws_manager import manager
        
        # Create a new instance
        new_manager = ConnectionManager()
        
        # They should be different instances
        assert manager is not new_manager
        
        # But the global manager should be the same
        from src.backend.services.ws_manager import manager as manager2
        assert manager is manager2
