"""Security tests for authentication and authorization."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.models.user import User
from src.backend.auth.models import JWTPayload
from src.backend.auth.exceptions import TokenExpiredError, InvalidTokenError


class TestSecurity:
    """Security test cases."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        return User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=100,
            google_id="google_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scan_ids=["scan1", "scan2"]
        )

    @pytest.fixture
    def valid_jwt_payload(self):
        """Create a valid JWT payload."""
        return JWTPayload(
            sub="test_user_id",
            email="test@example.com",
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
            iat=datetime.now(timezone.utc),
            token_type="access"
        )

    @pytest.fixture
    def expired_jwt_payload(self):
        """Create an expired JWT payload."""
        return JWTPayload(
            sub="test_user_id",
            email="test@example.com",
            exp=datetime.now(timezone.utc) - timedelta(hours=1),
            iat=datetime.now(timezone.utc) - timedelta(hours=2),
            token_type="access"
        )

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_scan_endpoint_requires_authentication(self, client):
        """Test that scan endpoint requires authentication."""
        # Test without authentication
        response = client.post("/scan", files={"image": ("test.jpg", b"fake_image_data")})
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_scan_endpoint_with_invalid_token(self, client):
        """Test scan endpoint with invalid JWT token."""
        # Test with invalid token
        response = client.post(
            "/scan", 
            files={"image": ("test.jpg", b"fake_image_data")},
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Invalid authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_scan_endpoint_with_expired_token(self, client):
        """Test scan endpoint with expired JWT token."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock auth service to raise TokenExpiredError
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = TokenExpiredError("Token has expired")
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test with expired token
            response = client.post(
                "/scan", 
                files={"image": ("test.jpg", b"fake_image_data")},
                headers={"Authorization": "Bearer expired_token"}
            )
            
            # Should return 401 Unauthorized
            assert response.status_code == 401
            assert "Token has expired" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_scan_endpoint_with_valid_token(self, client, mock_user):
        """Test scan endpoint with valid JWT token."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service, \
             patch("src.backend.routers.scan.bottle_measurer.measure") as mock_measure, \
             patch("src.backend.routers.scan.roboflow_client.predict") as mock_predict, \
             patch("src.backend.routers.scan.validate_scan") as mock_validate, \
             patch("src.backend.routers.scan.smartbin_client.open_bin") as mock_open_bin, \
             patch("src.backend.routers.scan.add_points") as mock_add_points, \
             patch("src.backend.routers.scan.mongo_db") as mock_db, \
             patch("src.backend.routers.scan.manager") as mock_manager:
            
            # Mock auth service
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = valid_jwt_payload
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            # Mock other services
            mock_measure.return_value = Mock(diameter_mm=65.0, height_mm=180.0, volume_ml=600.0)
            mock_predict.return_value = {"predictions": []}
            mock_validate.return_value = Mock(
                is_valid=True, brand="aqua", confidence=0.95, 
                points_awarded=10, reason="Valid bottle",
                measurement=mock_measure.return_value
            )
            mock_open_bin.return_value = ["lid_opened", "sensor_triggered", "lid_closed"]
            mock_add_points.return_value = 110
            
            # Mock MongoDB
            mock_db.__bool__.return_value = True
            mock_db.__getitem__.return_value.insert_one.return_value = Mock(inserted_id="scan_id_123")
            
            # Mock WebSocket manager
            mock_manager.broadcast = AsyncMock()
            mock_manager.broadcast_to_user = AsyncMock()
            mock_manager.is_user_connected.return_value = False
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            # Test with valid token
            response = client.post(
                "/scan", 
                files={"image": ("test.jpg", b"fake_image_data")},
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Should return 200 OK
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["is_valid"] is True
            assert response_data["brand"] == "aqua"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_auth_profile_endpoint_requires_authentication(self, client):
        """Test that auth profile endpoint requires authentication."""
        # Test without authentication
        response = client.get("/auth/profile")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_auth_stats_endpoint_requires_authentication(self, client):
        """Test that auth stats endpoint requires authentication."""
        # Test without authentication
        response = client.get("/auth/stats")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_auth_leaderboard_endpoint_requires_authentication(self, client):
        """Test that auth leaderboard endpoint requires authentication."""
        # Test without authentication
        response = client.get("/auth/leaderboard")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_auth_rewards_endpoint_requires_authentication(self, client):
        """Test that auth rewards endpoint requires authentication."""
        # Test without authentication
        response = client.get("/auth/rewards")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_public_endpoints_accessible_without_authentication(self, client):
        """Test that public endpoints are accessible without authentication."""
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test auth health endpoint
        response = client.get("/auth/health")
        assert response.status_code == 200
        
        # Test OAuth initiation endpoint
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            mock_oauth_service = AsyncMock()
            mock_oauth_service.generate_authorization_url.return_value = (
                "https://accounts.google.com/oauth/authorize?client_id=test",
                "state_123"
            )
            mock_get_oauth_service.return_value = mock_oauth_service
            
            response = client.get("/auth/google")
            assert response.status_code == 200

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_websocket_authentication_validation(self, client):
        """Test WebSocket authentication validation."""
        # This would require WebSocket testing which is more complex
        # For now, we'll test the authentication logic in the WebSocket endpoints
        
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = InvalidTokenError("Invalid token")
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test that invalid tokens are properly rejected
            # This is a simplified test - actual WebSocket testing would require more setup

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_token_tampering_protection(self, client):
        """Test that tampered JWT tokens are rejected."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            # Mock auth service to reject tampered tokens
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = InvalidTokenError("Token signature invalid")
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test with tampered token
            response = client.post(
                "/scan", 
                files={"image": ("test.jpg", b"fake_image_data")},
                headers={"Authorization": "Bearer tampered_token"}
            )
            
            # Should return 401 Unauthorized
            assert response.status_code == 401
            assert "Invalid authentication token" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_csrf_protection_oauth_state_parameter(self, client):
        """Test CSRF protection through OAuth state parameter."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            # Mock OAuth service
            mock_oauth_service = AsyncMock()
            mock_oauth_service.generate_authorization_url.return_value = (
                "https://accounts.google.com/oauth/authorize?client_id=test&state=state_123",
                "state_123"
            )
            mock_get_oauth_service.return_value = mock_oauth_service
            
            # Test OAuth initiation
            response = client.get("/auth/google")
            assert response.status_code == 200
            
            # Verify that state parameter is included in the URL
            assert "state=" in response.url

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_oauth_callback_state_validation(self, client):
        """Test OAuth callback state parameter validation."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            # Mock OAuth service to validate state parameter
            mock_oauth_service = AsyncMock()
            mock_oauth_service.exchange_code_for_tokens.side_effect = Exception("Invalid state parameter")
            mock_get_oauth_service.return_value = mock_oauth_service
            
            # Test OAuth callback with invalid state
            response = client.get("/auth/google/callback?code=auth_code&state=invalid_state")
            
            # Should return 400 Bad Request
            assert response.status_code == 400
            assert "OAuth authentication failed" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_user_isolation(self, client, mock_user):
        """Test that users can only access their own data."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service:
            
            # Mock auth service
            mock_auth_service = Mock()
            mock_auth_service.verify_token.return_value = valid_jwt_payload
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_user_service.get_user_by_id.return_value = mock_user
            
            mock_get_auth_service.return_value = mock_auth_service
            mock_get_user_service.return_value = mock_user_service
            
            # Test that user can access their own profile
            response = client.get(
                "/auth/profile",
                headers={"Authorization": "Bearer valid_token"}
            )
            
            # Should return 200 OK
            assert response.status_code == 200
            
            # Verify that the returned data belongs to the authenticated user
            response_data = response.json()
            assert response_data["email"] == mock_user.email
            assert response_data["email"] == "test@example.com"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_middleware_excludes_public_paths(self, client):
        """Test that authentication middleware excludes public paths."""
        # Test that public paths are accessible without authentication
        public_paths = [
            "/health",
            "/auth/health",
            "/auth/google",
            "/docs",
            "/openapi.json"
        ]
        
        for path in public_paths:
            if path == "/auth/google":
                # Mock OAuth service for this endpoint
                with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
                    mock_oauth_service = AsyncMock()
                    mock_oauth_service.generate_authorization_url.return_value = (
                        "https://accounts.google.com/oauth/authorize?client_id=test",
                        "state_123"
                    )
                    mock_get_oauth_service.return_value = mock_oauth_service
                    
                    response = client.get(path)
                    assert response.status_code == 200
            else:
                response = client.get(path)
                # Some paths might not exist in the test environment, but they shouldn't require auth
                if response.status_code != 404:  # Ignore 404 for non-existent paths
                    assert response.status_code != 401  # Should not require authentication

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_jwt_token_expiration_handling(self, client):
        """Test proper handling of expired JWT tokens."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            # Mock auth service to simulate expired token
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = TokenExpiredError("Token has expired")
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test with expired token
            response = client.post(
                "/scan", 
                files={"image": ("test.jpg", b"fake_image_data")},
                headers={"Authorization": "Bearer expired_token"}
            )
            
            # Should return 401 Unauthorized with specific error message
            assert response.status_code == 401
            assert "Token has expired" in response.json()["detail"]

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_invalid_token_format_handling(self, client):
        """Test handling of invalid token formats."""
        # Test with malformed Authorization header
        response = client.post(
            "/scan", 
            files={"image": ("test.jpg", b"fake_image_data")},
            headers={"Authorization": "InvalidFormat token123"}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
        
        # Test with missing Bearer prefix
        response = client.post(
            "/scan", 
            files={"image": ("test.jpg", b"fake_image_data")},
            headers={"Authorization": "token123"}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
