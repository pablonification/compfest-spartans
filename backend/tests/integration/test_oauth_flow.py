"""Integration tests for OAuth flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.backend.main import app
from src.backend.models.user import User
from src.backend.auth.models import GoogleUserInfo, OAuthToken


class TestOAuthFlowIntegration:
    """Integration tests for OAuth authentication flow."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_google_user_info(self):
        """Create mock Google user info."""
        return GoogleUserInfo(
            sub="google_user_123",
            email="test@example.com",
            name="Test User",
            given_name="Test",
            family_name="User",
            picture="https://example.com/avatar.jpg",
            email_verified=True
        )

    @pytest.fixture
    def mock_oauth_tokens(self):
        """Create mock OAuth tokens."""
        return OAuthToken(
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            token_type="Bearer",
            expires_in=3600
        )

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        return User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=0,
            google_id="google_user_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scan_ids=[]
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_initiation_success(self, client):
        """Test successful OAuth initiation."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            # Mock OAuth service
            mock_oauth_service = AsyncMock()
            mock_oauth_service.generate_authorization_url.return_value = (
                "https://accounts.google.com/oauth/authorize?client_id=test&response_type=code&scope=openid%20email%20profile&redirect_uri=http%3A//localhost%3A8000/auth/google/callback&state=state_123",
                "state_123"
            )
            mock_get_oauth_service.return_value = mock_oauth_service
            
            # Test OAuth initiation
            response = client.get("/auth/google")
            
            # Verify response
            assert response.status_code == 200
            assert "accounts.google.com" in response.url
            
            # Verify OAuth service was called
            mock_oauth_service.generate_authorization_url.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_initiation_failure(self, client):
        """Test OAuth initiation failure."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            # Mock OAuth service failure
            mock_oauth_service = AsyncMock()
            mock_oauth_service.generate_authorization_url.side_effect = Exception("OAuth service error")
            mock_get_oauth_service.return_value = mock_oauth_service
            
            # Test OAuth initiation
            response = client.get("/auth/google")
            
            # Verify error response
            assert response.status_code == 500
            assert "Failed to initiate OAuth login" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_callback_success_new_user(self, client, mock_google_user_info, 
                                                 mock_oauth_tokens, mock_user):
        """Test successful OAuth callback for new user."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock OAuth service
            mock_oauth_service = AsyncMock()
            mock_oauth_service.exchange_code_for_tokens.return_value = mock_oauth_tokens
            mock_oauth_service.get_user_info.return_value = mock_google_user_info
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_user_service.get_or_create_user_from_oauth.return_value = mock_user
            mock_user_service.update_user_last_login.return_value = True
            
            # Mock auth service
            mock_auth_service = Mock()
            mock_auth_service.create_access_token.return_value = "jwt_access_token_123"
            mock_auth_service.create_refresh_token.return_value = "jwt_refresh_token_123"
            
            mock_get_oauth_service.return_value = mock_oauth_service
            mock_get_user_service.return_value = mock_user_service
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test OAuth callback
            response = client.get("/auth/google/callback?code=auth_code_123&state=state_123")
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            
            assert "access_token" in response_data
            assert "refresh_token" in response_data
            assert response_data["token_type"] == "bearer"
            assert "user" in response_data
            assert response_data["user"]["email"] == "test@example.com"
            assert response_data["user"]["id"] == "test_user_id"
            
            # Verify services were called
            mock_oauth_service.exchange_code_for_tokens.assert_called_once_with("auth_code_123", "state_123")
            mock_oauth_service.get_user_info.assert_called_once_with("access_token_123")
            mock_user_service.get_or_create_user_from_oauth.assert_called_once_with(mock_google_user_info)
            mock_user_service.update_user_last_login.assert_called_once_with("test_user_id")
            mock_auth_service.create_access_token.assert_called_once_with("test_user_id", "test@example.com")
            mock_auth_service.create_refresh_token.assert_called_once_with("test_user_id", "test@example.com")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_callback_success_existing_user(self, client, mock_google_user_info, 
                                                      mock_oauth_tokens, mock_user):
        """Test successful OAuth callback for existing user."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock OAuth service
            mock_oauth_service = AsyncMock()
            mock_oauth_service.exchange_code_for_tokens.return_value = mock_oauth_tokens
            mock_oauth_service.get_user_info.return_value = mock_google_user_info
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_user_service.get_or_create_user_from_oauth.return_value = mock_user
            mock_user_service.update_user_last_login.return_value = True
            
            # Mock auth service
            mock_auth_service = Mock()
            mock_auth_service.create_access_token.return_value = "jwt_access_token_123"
            mock_auth_service.create_refresh_token.return_value = "jwt_refresh_token_123"
            
            mock_get_oauth_service.return_value = mock_oauth_service
            mock_get_user_service.return_value = mock_user_service
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test OAuth callback
            response = client.get("/auth/google/callback?code=auth_code_123&state=state_123")
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            
            assert "access_token" in response_data
            assert "refresh_token" in response_data
            assert "user" in response_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_callback_failure(self, client):
        """Test OAuth callback failure."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            # Mock OAuth service failure
            mock_oauth_service = AsyncMock()
            mock_oauth_service.exchange_code_for_tokens.side_effect = Exception("OAuth callback error")
            mock_get_oauth_service.return_value = mock_oauth_service
            
            # Test OAuth callback
            response = client.get("/auth/google/callback?code=auth_code_123&state=state_123")
            
            # Verify error response
            assert response.status_code == 400
            assert "OAuth authentication failed" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_refresh_success(self, client):
        """Test successful token refresh."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            # Mock auth service
            mock_auth_service = Mock()
            mock_jwt_payload = Mock()
            mock_jwt_payload.sub = "test_user_id"
            mock_jwt_payload.email = "test@example.com"
            
            mock_auth_service.verify_token.return_value = mock_jwt_payload
            mock_auth_service.create_access_token.return_value = "new_access_token_123"
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test token refresh
            response = client.post("/auth/refresh", headers={"X-Refresh-Token": "refresh_token_123"})
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            
            assert "access_token" in response_data
            assert response_data["access_token"] == "new_access_token_123"
            assert response_data["token_type"] == "bearer"
            
            # Verify auth service was called
            mock_auth_service.verify_token.assert_called_once_with("refresh_token_123", "refresh")
            mock_auth_service.create_access_token.assert_called_once_with("test_user_id", "test@example.com")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_refresh_missing_token(self, client):
        """Test token refresh with missing refresh token."""
        # Test token refresh without header
        response = client.post("/auth/refresh")
        
        # Verify error response
        assert response.status_code == 400
        assert "Refresh token required" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, client):
        """Test token refresh with invalid refresh token."""
        with patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            # Mock auth service failure
            mock_auth_service = Mock()
            mock_auth_service.verify_token.side_effect = Exception("Invalid token")
            
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test token refresh
            response = client.post("/auth/refresh", headers={"X-Refresh-Token": "invalid_token"})
            
            # Verify error response
            assert response.status_code == 401
            assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        """Test successful logout."""
        # Test logout
        response = client.post("/auth/logout")
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        assert "message" in response_data
        assert "Logout successful" in response_data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock services
            mock_oauth_service = Mock()
            mock_auth_service = Mock()
            mock_auth_service.algorithm = "HS256"
            
            mock_get_oauth_service.return_value = mock_oauth_service
            mock_get_auth_service.return_value = mock_auth_service
            
            # Test health check
            response = client.get("/auth/health")
            
            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            
            assert response_data["status"] == "healthy"
            assert response_data["service"] == "authentication"
            assert response_data["oauth_provider"] == "google"
            assert response_data["jwt_algorithm"] == "HS256"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test health check failure."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service:
            # Mock service failure
            mock_oauth_service = Mock()
            mock_oauth_service.side_effect = Exception("Service error")
            
            mock_get_oauth_service.return_value = mock_oauth_service
            
            # Test health check
            response = client.get("/auth/health")
            
            # Verify error response
            assert response.status_code == 503
            assert "Authentication service unhealthy" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_flow_end_to_end(self, client, mock_google_user_info, 
                                       mock_oauth_tokens, mock_user):
        """Test complete OAuth flow end-to-end."""
        with patch("src.backend.services.service_factory.get_oauth_service") as mock_get_oauth_service, \
             patch("src.backend.services.service_factory.get_user_service") as mock_get_user_service, \
             patch("src.backend.services.service_factory.get_auth_service") as mock_get_auth_service:
            
            # Mock OAuth service
            mock_oauth_service = AsyncMock()
            mock_oauth_service.generate_authorization_url.return_value = (
                "https://accounts.google.com/oauth/authorize?client_id=test&response_type=code&scope=openid%20email%20profile&redirect_uri=http%3A//localhost%3A8000/auth/google/callback&state=state_123",
                "state_123"
            )
            mock_oauth_service.exchange_code_for_tokens.return_value = mock_oauth_tokens
            mock_oauth_service.get_user_info.return_value = mock_google_user_info
            
            # Mock user service
            mock_user_service = AsyncMock()
            mock_user_service.get_or_create_user_from_oauth.return_value = mock_user
            mock_user_service.update_user_last_login.return_value = True
            
            # Mock auth service
            mock_auth_service = Mock()
            mock_auth_service.create_access_token.return_value = "jwt_access_token_123"
            mock_auth_service.create_refresh_token.return_value = "jwt_refresh_token_123"
            mock_auth_service.algorithm = "HS256"
            
            mock_get_oauth_service.return_value = mock_oauth_service
            mock_get_user_service.return_value = mock_user_service
            mock_get_auth_service.return_value = mock_auth_service
            
            # Step 1: Initiate OAuth
            response1 = client.get("/auth/google")
            assert response1.status_code == 200
            
            # Step 2: OAuth callback
            response2 = client.get("/auth/google/callback?code=auth_code_123&state=state_123")
            assert response2.status_code == 200
            response_data = response2.json()
            
            access_token = response_data["access_token"]
            refresh_token = response_data["refresh_token"]
            
            # Step 3: Test token refresh
            response3 = client.post("/auth/refresh", headers={"X-Refresh-Token": refresh_token})
            assert response3.status_code == 200
            
            # Step 4: Test health check
            response4 = client.get("/auth/health")
            assert response4.status_code == 200
            
            # Step 5: Test logout
            response5 = client.post("/auth/logout")
            assert response5.status_code == 200
            
            # Verify all services were called correctly
            mock_oauth_service.generate_authorization_url.assert_called_once()
            mock_oauth_service.exchange_code_for_tokens.assert_called_once()
            mock_oauth_service.get_user_info.assert_called_once()
            mock_user_service.get_or_create_user_from_oauth.assert_called_once()
            mock_user_service.update_user_last_login.assert_called_once()
            mock_auth_service.create_access_token.assert_called_once()
            mock_auth_service.create_refresh_token.assert_called_once()
