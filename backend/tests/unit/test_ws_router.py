"""Unit tests for WebSocket router."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.testclient import TestClient

from src.backend.routers.ws import websocket_status_endpoint, websocket_user_endpoint
from src.backend.models.user import User


class TestWebSocketRouter:
    """Test cases for WebSocket router."""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing."""
        websocket = AsyncMock(spec=WebSocket)
        websocket.send_json = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.close = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        return User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=100,
            google_id="google_123",
            created_at=Mock(),
            updated_at=Mock(),
            scan_ids=["scan1", "scan2"]
        )

    @pytest.fixture
    def mock_jwt_payload(self):
        """Create a mock JWT payload."""
        payload = Mock()
        payload.sub = "test_user_id"
        payload.email = "test@example.com"
        return payload

    @pytest.mark.asyncio
    async def test_websocket_status_anonymous_connection(self, mock_websocket):
        """Test anonymous WebSocket connection."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Test anonymous connection (no token)
            await websocket_status_endpoint(mock_websocket, token=None)
            
            # Verify connection was established
            mock_manager.connect.assert_called_once_with(mock_websocket, None)
            mock_websocket.send_json.assert_called_once()
            
            # Verify anonymous message was sent
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "connection_established"
            assert call_args["data"]["authenticated"] is False

    @pytest.mark.asyncio
    async def test_websocket_status_authenticated_connection(self, mock_websocket, mock_user, mock_jwt_payload):
        """Test authenticated WebSocket connection."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Test authenticated connection
            await websocket_status_endpoint(mock_websocket, token="valid_token")
            
            # Verify connection was established with user ID
            mock_manager.connect.assert_called_once_with(mock_websocket, "test_user_id")
            mock_websocket.send_json.assert_called_once()
            
            # Verify authenticated message was sent
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "connection_established"
            assert call_args["data"]["authenticated"] is True
            assert call_args["data"]["user_id"] == "test_user_id"

    @pytest.mark.asyncio
    async def test_websocket_status_authentication_failure_continues_anonymous(self, mock_websocket):
        """Test that WebSocket continues as anonymous when authentication fails."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock auth service failure
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = Exception("Invalid token")
            
            mock_get_auth_service.return_value = mock_auth_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Test connection with invalid token
            await websocket_status_endpoint(mock_websocket, token="invalid_token")
            
            # Verify connection was established as anonymous
            mock_manager.connect.assert_called_once_with(mock_websocket, None)
            mock_websocket.send_json.assert_called_once()
            
            # Verify anonymous message was sent
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["data"]["authenticated"] is False

    @pytest.mark.asyncio
    async def test_websocket_status_user_not_found_continues_anonymous(self, mock_websocket, mock_jwt_payload):
        """Test that WebSocket continues as anonymous when user is not found."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = None  # User not found
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Test connection with valid token but user not found
            await websocket_status_endpoint(mock_websocket, token="valid_token")
            
            # Verify connection was established as anonymous
            mock_manager.connect.assert_called_once_with(mock_websocket, None)
            mock_websocket.send_json.assert_called_once()
            
            # Verify anonymous message was sent
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["data"]["authenticated"] is False

    @pytest.mark.asyncio
    async def test_websocket_status_handles_ping_pong(self, mock_websocket):
        """Test that WebSocket handles ping/pong messages."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Mock receive_text to return "ping" then disconnect
            mock_websocket.receive_text.side_effect = ["ping", WebSocketDisconnect()]
            
            await websocket_status_endpoint(mock_websocket, token=None)
            
            # Verify pong was sent
            mock_websocket.send_text.assert_called_once_with("pong")

    @pytest.mark.asyncio
    async def test_websocket_status_handles_stats_request(self, mock_websocket):
        """Test that WebSocket handles stats request."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager:
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            mock_manager.get_total_connection_count.return_value = 5
            mock_manager.get_authenticated_user_count.return_value = 3
            mock_manager.get_user_connection_count.return_value = 1
            
            # Mock receive_text to return "stats" then disconnect
            mock_websocket.receive_text.side_effect = ["stats", WebSocketDisconnect()]
            
            await websocket_status_endpoint(mock_websocket, token=None)
            
            # Verify stats were sent
            mock_websocket.send_json.assert_called()
            call_args = mock_websocket.send_json.call_args_list[1][0][0]  # Second call (after connection)
            assert call_args["type"] == "connection_stats"
            assert call_args["data"]["total_connections"] == 5
            assert call_args["data"]["authenticated_users"] == 3

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_success(self, mock_websocket, mock_user, mock_jwt_payload):
        """Test successful user-specific WebSocket connection."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Test user-specific connection
            await websocket_user_endpoint(mock_websocket, "test_user_id", "valid_token")
            
            # Verify connection was established
            mock_manager.connect.assert_called_once_with(mock_websocket, "test_user_id")
            mock_websocket.send_json.assert_called_once()
            
            # Verify user-specific message was sent
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "user_connection_established"
            assert call_args["data"]["user_id"] == "test_user_id"
            assert call_args["data"]["user_email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_unauthorized_access(self, mock_websocket, mock_jwt_payload):
        """Test that user cannot access another user's WebSocket."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock auth service
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload  # user_id = "test_user_id"
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test accessing different user's WebSocket
            await websocket_user_endpoint(mock_websocket, "different_user_id", "valid_token")
            
            # Verify connection was closed with policy violation
            mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_user_not_found(self, mock_websocket, mock_jwt_payload):
        """Test that WebSocket is closed when user is not found."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = None  # User not found
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            # Test connection with user not found
            await websocket_user_endpoint(mock_websocket, "test_user_id", "valid_token")
            
            # Verify connection was closed with policy violation
            mock_websocket.close.assert_called_once_with(code=status.WS_1008_POLICY_VIOLATION)

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_handles_ping_pong(self, mock_websocket, mock_user, mock_jwt_payload):
        """Test that user WebSocket handles ping/pong messages."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Mock receive_text to return "ping" then disconnect
            mock_websocket.receive_text.side_effect = ["ping", WebSocketDisconnect()]
            
            await websocket_user_endpoint(mock_websocket, "test_user_id", "valid_token")
            
            # Verify pong was sent
            mock_websocket.send_text.assert_called_once_with("pong")

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_handles_user_stats_request(self, mock_websocket, mock_user, mock_jwt_payload):
        """Test that user WebSocket handles user stats request."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service, \
             patch("src.backend.services.reward_service.get_user_stats") as mock_get_user_stats:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Mock user stats
            mock_user_stats = {
                "email": "test@example.com",
                "points": 100,
                "scan_count": 2,
                "total_rewards": 100
            }
            mock_get_user_stats.return_value = mock_user_stats
            
            # Mock receive_text to return "user_stats" then disconnect
            mock_websocket.receive_text.side_effect = ["user_stats", WebSocketDisconnect()]
            
            await websocket_user_endpoint(mock_websocket, "test_user_id", "valid_token")
            
            # Verify user stats were sent
            mock_websocket.send_json.assert_called()
            call_args = mock_websocket.send_json.call_args_list[1][0][0]  # Second call (after connection)
            assert call_args["type"] == "user_stats"
            assert call_args["data"] == mock_user_stats

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_handles_disconnect(self, mock_websocket, mock_user, mock_jwt_payload):
        """Test that user WebSocket properly handles disconnect."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock services
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            mock_manager.connect = AsyncMock()
            mock_manager.disconnect = Mock()
            
            # Mock receive_text to disconnect immediately
            mock_websocket.receive_text.side_effect = WebSocketDisconnect()
            
            await websocket_user_endpoint(mock_websocket, "test_user_id", "valid_token")
            
            # Verify disconnect was handled
            mock_manager.disconnect.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_handles_exception(self, mock_websocket, mock_jwt_payload):
        """Test that user WebSocket properly handles exceptions."""
        with patch("src.backend.services.ws_manager.manager") as mock_manager, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock auth service to raise exception
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = Exception("Auth service error")
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test connection with auth service error
            await websocket_user_endpoint(mock_websocket, "test_user_id", "valid_token")
            
            # Verify connection was closed with internal error
            mock_websocket.close.assert_called_once_with(code=status.WS_1011_INTERNAL_ERROR)
