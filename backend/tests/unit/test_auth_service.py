"""Unit tests for JWT authentication service."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from jose import JWTError

from src.backend.services.auth_service import JWTAuthService
from src.backend.auth.models import JWTPayload, TokenResponse
from src.backend.auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError
)


class TestJWTAuthService:
    """Test JWT authentication service functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('src.backend.services.auth_service.get_settings') as mock:
            mock.return_value.JWT_SECRET_KEY = "test_secret_key_123"
            mock.return_value.JWT_ALGORITHM = "HS256"
            mock.return_value.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            mock.return_value.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
            yield mock.return_value
    
    @pytest.fixture
    def auth_service(self, mock_settings):
        """Create JWT auth service instance for testing."""
        return JWTAuthService()
    
    def test_auth_service_initialization(self, mock_settings):
        """Test JWT auth service initialization with valid settings."""
        service = JWTAuthService()
        assert service.settings == mock_settings
    
    def test_auth_service_initialization_warning_default_secret(self):
        """Test JWT auth service initialization with default secret key warning."""
        with patch('src.backend.services.auth_service.get_settings') as mock:
            mock.return_value.JWT_SECRET_KEY = "your-secret-key-change-in-production"
            mock.return_value.JWT_ALGORITHM = "HS256"
            mock.return_value.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            mock.return_value.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
            
            # Should not raise exception, just log warnings
            service = JWTAuthService()
            assert service.settings == mock.return_value
    
    def test_create_access_token_success(self, auth_service):
        """Test successful access token creation."""
        user_id = "user123"
        email = "test@example.com"
        
        token = auth_service.create_access_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = auth_service.verify_token(token, "access")
        assert decoded.sub == user_id
        assert decoded.email == email
        assert decoded.token_type == "access"
    
    def test_create_access_token_failure(self, auth_service):
        """Test access token creation failure."""
        with patch('jose.jwt.encode') as mock_encode:
            mock_encode.side_effect = Exception("JWT encoding failed")
            
            with pytest.raises(AuthenticationError, match="Failed to create access token"):
                auth_service.create_access_token("user123", "test@example.com")
    
    def test_create_refresh_token_success(self, auth_service):
        """Test successful refresh token creation."""
        user_id = "user123"
        email = "test@example.com"
        
        token = auth_service.create_refresh_token(user_id, email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = auth_service.verify_token(token, "refresh")
        assert decoded.sub == user_id
        assert decoded.email == email
        assert decoded.token_type == "refresh"
    
    def test_create_refresh_token_failure(self, auth_service):
        """Test refresh token creation failure."""
        with patch('jose.jwt.encode') as mock_encode:
            mock_encode.side_effect = Exception("JWT encoding failed")
            
            with pytest.raises(AuthenticationError, match="Failed to create refresh token"):
                auth_service.create_refresh_token("user123", "test@example.com")
    
    def test_create_token_pair_success(self, auth_service):
        """Test successful token pair creation."""
        user_id = "user123"
        email = "test@example.com"
        name = "Test User"
        
        token_response = auth_service.create_token_pair(user_id, email, name)
        
        assert isinstance(token_response, TokenResponse)
        assert token_response.user_id == user_id
        assert token_response.email == email
        assert token_response.name == name
        assert token_response.token_type == "Bearer"
        assert token_response.expires_in == 30 * 60  # 30 minutes in seconds
        
        # Verify both tokens are valid
        access_payload = auth_service.verify_token(token_response.access_token, "access")
        refresh_payload = auth_service.verify_token(token_response.refresh_token, "refresh")
        
        assert access_payload.sub == user_id
        assert refresh_payload.sub == user_id
    
    def test_verify_token_success(self, auth_service):
        """Test successful token verification."""
        # Create a valid token first
        token = auth_service.create_access_token("user123", "test@example.com")
        
        payload = auth_service.verify_token(token, "access")
        
        assert isinstance(payload, JWTPayload)
        assert payload.sub == "user123"
        assert payload.email == "test@example.com"
        assert payload.token_type == "access"
    
    def test_verify_token_invalid_format(self, auth_service):
        """Test token verification with invalid format."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            auth_service.verify_token("invalid.token.format", "access")
    
    def test_verify_token_wrong_type(self, auth_service):
        """Test token verification with wrong token type."""
        # Create an access token but try to verify as refresh
        token = auth_service.create_access_token("user123", "test@example.com")
        
        with pytest.raises(InvalidTokenError, match="Invalid token type"):
            auth_service.verify_token(token, "refresh")
    
    def test_verify_token_expired(self, auth_service):
        """Test token verification with expired token."""
        # Create a token with very short expiration
        with patch.object(auth_service.settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 0):
            token = auth_service.create_access_token("user123", "test@example.com")
        
        # Wait a moment to ensure expiration
        import time
        time.sleep(0.1)
        
        with pytest.raises(TokenExpiredError, match="Token has expired"):
            auth_service.verify_token(token, "access")
    
    def test_verify_token_missing_payload_fields(self, auth_service):
        """Test token verification with missing payload fields."""
        # Create a token manually with missing fields
        payload = {
            "sub": "user123",
            # Missing email, exp, iat, token_type
        }
        
        token = auth_service.settings.JWT_SECRET_KEY
        with patch('jose.jwt.decode') as mock_decode:
            mock_decode.return_value = payload
            
            with pytest.raises(InvalidTokenError, match="Invalid token type"):
                auth_service.verify_token(token, "access")
    
    def test_refresh_access_token_success(self, auth_service):
        """Test successful access token refresh."""
        # Create a valid refresh token
        refresh_token = auth_service.create_refresh_token("user123", "test@example.com")
        
        new_access_token = auth_service.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert len(new_access_token) > 0
        
        # Verify the new token
        payload = auth_service.verify_token(new_access_token, "access")
        assert payload.sub == "user123"
        assert payload.email == "test@example.com"
    
    def test_refresh_access_token_invalid_refresh(self, auth_service):
        """Test access token refresh with invalid refresh token."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            auth_service.refresh_access_token("invalid.refresh.token")
    
    def test_refresh_access_token_expired_refresh(self, auth_service):
        """Test access token refresh with expired refresh token."""
        # Create an expired refresh token
        with patch.object(auth_service.settings, 'JWT_REFRESH_TOKEN_EXPIRE_DAYS', 0):
            refresh_token = auth_service.create_refresh_token("user123", "test@example.com")
        
        # Wait a moment to ensure expiration
        import time
        time.sleep(0.1)
        
        with pytest.raises(TokenExpiredError, match="Token has expired"):
            auth_service.refresh_access_token(refresh_token)
    
    def test_extract_user_from_token_success(self, auth_service):
        """Test successful user extraction from token."""
        # Create a valid access token
        token = auth_service.create_access_token("user123", "test@example.com")
        
        user_id, email = auth_service.extract_user_from_token(token)
        
        assert user_id == "user123"
        assert email == "test@example.com"
    
    def test_extract_user_from_token_invalid(self, auth_service):
        """Test user extraction from invalid token."""
        with pytest.raises(InvalidTokenError, match="Invalid token format"):
            auth_service.extract_user_from_token("invalid.token")
    
    def test_is_token_expired_true(self, auth_service):
        """Test token expiration check for expired token."""
        # Create an expired token
        with patch.object(auth_service.settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 0):
            token = auth_service.create_access_token("user123", "test@example.com")
        
        # Wait a moment to ensure expiration
        import time
        time.sleep(0.1)
        
        assert auth_service.is_token_expired(token) is True
    
    def test_is_token_expired_false(self, auth_service):
        """Test token expiration check for valid token."""
        token = auth_service.create_access_token("user123", "test@example.com")
        assert auth_service.is_token_expired(token) is False
    
    def test_is_token_expired_invalid_token(self, auth_service):
        """Test token expiration check for invalid token."""
        assert auth_service.is_token_expired("invalid.token") is True
    
    def test_token_expiration_times(self, auth_service):
        """Test that tokens have correct expiration times."""
        user_id = "user123"
        email = "test@example.com"
        
        # Test access token expiration
        access_token = auth_service.create_access_token(user_id, email)
        access_payload = auth_service.verify_token(access_token, "access")
        
        # Check that expiration is roughly 30 minutes from now
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=30)
        actual_exp = datetime.fromtimestamp(access_payload.exp, timezone.utc)
        
        # Allow 1 second tolerance
        assert abs((expected_exp - actual_exp).total_seconds()) < 1
        
        # Test refresh token expiration
        refresh_token = auth_service.create_refresh_token(user_id, email)
        refresh_payload = auth_service.verify_token(refresh_token, "refresh")
        
        # Check that expiration is roughly 7 days from now
        expected_exp = datetime.now(timezone.utc) + timedelta(days=7)
        actual_exp = datetime.fromtimestamp(refresh_payload.exp, timezone.utc)
        
        # Allow 1 second tolerance
        assert abs((expected_exp - actual_exp).total_seconds()) < 1
