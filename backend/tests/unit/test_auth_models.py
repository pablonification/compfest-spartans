"""Unit tests for authentication models."""

import pytest
from datetime import datetime, timezone

from src.backend.auth.models import (
    OAuthToken,
    GoogleUserInfo,
    JWTPayload,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
)


class TestOAuthToken:
    """Test OAuth token model."""
    
    def test_oauth_token_creation(self):
        """Test OAuth token creation with required fields."""
        token = OAuthToken(
            access_token="test_access_token",
            expires_in=3600,
            scope="openid email profile"
        )
        
        assert token.access_token == "test_access_token"
        assert token.expires_in == 3600
        assert token.scope == "openid email profile"
        assert token.token_type == "Bearer"
        assert isinstance(token.created_at, datetime)
    
    def test_oauth_token_with_refresh_token(self):
        """Test OAuth token creation with refresh token."""
        token = OAuthToken(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=3600,
            scope="openid email profile"
        )
        
        assert token.refresh_token == "test_refresh_token"


class TestGoogleUserInfo:
    """Test Google user info model."""
    
    def test_google_user_info_creation(self):
        """Test Google user info creation with required fields."""
        user_info = GoogleUserInfo(
            sub="123456789",
            email="test@example.com",
            email_verified=True
        )
        
        assert user_info.sub == "123456789"
        assert user_info.email == "test@example.com"
        assert user_info.email_verified is True
    
    def test_google_user_info_with_optional_fields(self):
        """Test Google user info creation with optional fields."""
        user_info = GoogleUserInfo(
            sub="123456789",
            email="test@example.com",
            email_verified=True,
            name="Test User",
            picture="https://example.com/avatar.jpg"
        )
        
        assert user_info.name == "Test User"
        assert user_info.picture == "https://example.com/avatar.jpg"


class TestJWTPayload:
    """Test JWT payload model."""
    
    def test_jwt_payload_creation(self):
        """Test JWT payload creation."""
        now = int(datetime.now(timezone.utc).timestamp())
        payload = JWTPayload(
            sub="user123",
            email="test@example.com",
            exp=now + 3600,
            iat=now
        )
        
        assert payload.sub == "user123"
        assert payload.email == "test@example.com"
        assert payload.exp > now
        assert payload.iat == now
        assert payload.token_type == "access"


class TestTokenResponse:
    """Test token response model."""
    
    def test_token_response_creation(self):
        """Test token response creation."""
        response = TokenResponse(
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            expires_in=1800,
            user_id="user123",
            email="test@example.com"
        )
        
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_123"
        assert response.expires_in == 1800
        assert response.user_id == "user123"
        assert response.email == "test@example.com"
        assert response.token_type == "Bearer"


class TestRefreshTokenRequest:
    """Test refresh token request model."""
    
    def test_refresh_token_request_creation(self):
        """Test refresh token request creation."""
        request = RefreshTokenRequest(refresh_token="refresh_token_123")
        assert request.refresh_token == "refresh_token_123"


class TestLogoutRequest:
    """Test logout request model."""
    
    def test_logout_request_creation(self):
        """Test logout request creation."""
        request = LogoutRequest(refresh_token="refresh_token_123")
        assert request.refresh_token == "refresh_token_123"
