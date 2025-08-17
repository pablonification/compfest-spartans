"""Unit tests for Google OAuth service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from google.auth.exceptions import GoogleAuthError

from src.backend.services.oauth_service import GoogleOAuthService
from src.backend.auth.models import OAuthToken, GoogleUserInfo
from src.backend.auth.exceptions import OAuthError, OAuthCodeExchangeError


class TestGoogleOAuthService:
    """Test Google OAuth service functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('src.backend.services.oauth_service.get_settings') as mock:
            mock.return_value.GOOGLE_CLIENT_ID = "test_client_id"
            mock.return_value.GOOGLE_CLIENT_SECRET = "test_client_secret"
            mock.return_value.GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
            yield mock.return_value
    
    @pytest.fixture
    def oauth_service(self, mock_settings):
        """Create OAuth service instance for testing."""
        return GoogleOAuthService()
    
    @pytest.fixture
    def mock_flow(self):
        """Mock OAuth flow."""
        flow = Mock()
        flow.credentials = Mock()
        flow.credentials.token = "test_access_token"
        flow.credentials.refresh_token = "test_refresh_token"
        flow.credentials.expiry = None
        flow.credentials.scopes = ["openid", "email", "profile"]
        return flow
    
    def test_oauth_service_initialization(self, mock_settings):
        """Test OAuth service initialization with valid settings."""
        service = GoogleOAuthService()
        assert service.settings == mock_settings
    
    def test_oauth_service_initialization_missing_config(self):
        """Test OAuth service initialization with missing configuration."""
        with patch('src.backend.services.oauth_service.get_settings') as mock:
            mock.return_value.GOOGLE_CLIENT_ID = ""
            mock.return_value.GOOGLE_CLIENT_SECRET = ""
            mock.return_value.GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
            
            # Should not raise exception, just log warnings
            service = GoogleOAuthService()
            assert service.settings == mock.return_value
    
    def test_get_flow_creation(self, oauth_service, mock_flow):
        """Test OAuth flow creation."""
        with patch('src.backend.services.oauth_service.Flow') as mock_flow_class:
            mock_flow_class.from_client_config.return_value = mock_flow
            
            flow = oauth_service._get_flow()
            
            assert flow == mock_flow
            mock_flow_class.from_client_config.assert_called_once()
    
    def test_get_flow_caching(self, oauth_service, mock_flow):
        """Test that OAuth flow is cached after first creation."""
        with patch('src.backend.services.oauth_service.Flow') as mock_flow_class:
            mock_flow_class.from_client_config.return_value = mock_flow
            
            # First call should create flow
            flow1 = oauth_service._get_flow()
            # Second call should return cached flow
            flow2 = oauth_service._get_flow()
            
            assert flow1 == flow2
            # Flow should only be created once
            mock_flow_class.from_client_config.assert_called_once()
    
    def test_generate_authorization_url_success(self, oauth_service, mock_flow):
        """Test successful authorization URL generation."""
        with patch.object(oauth_service, '_get_flow') as mock_get_flow:
            mock_get_flow.return_value = mock_flow
            mock_flow.authorization_url.return_value = ("https://google.com/auth", {})
            
            auth_url, state = oauth_service.generate_authorization_url()
            
            assert auth_url == "https://google.com/auth"
            assert isinstance(state, str)
            assert len(state) > 0
            mock_flow.authorization_url.assert_called_once()
    
    def test_generate_authorization_url_failure(self, oauth_service):
        """Test authorization URL generation failure."""
        with patch.object(oauth_service, '_get_flow') as mock_get_flow:
            mock_get_flow.side_effect = Exception("Flow creation failed")
            
            with pytest.raises(OAuthError, match="Failed to generate authorization URL"):
                oauth_service.generate_authorization_url()
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, oauth_service, mock_flow):
        """Test successful code exchange for tokens."""
        with patch.object(oauth_service, '_get_flow') as mock_get_flow:
            mock_get_flow.return_value = mock_flow
            
            oauth_token = await oauth_service.exchange_code_for_tokens("test_code", "test_state")
            
            assert isinstance(oauth_token, OAuthToken)
            assert oauth_token.access_token == "test_access_token"
            assert oauth_token.refresh_token == "test_refresh_token"
            assert oauth_token.token_type == "Bearer"
            mock_flow.fetch_token.assert_called_once_with(code="test_code")
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_failure(self, oauth_service):
        """Test code exchange failure."""
        with patch.object(oauth_service, '_get_flow') as mock_get_flow:
            mock_get_flow.side_effect = Exception("Token exchange failed")
            
            with pytest.raises(OAuthCodeExchangeError, match="Failed to exchange authorization code for tokens"):
                await oauth_service.exchange_code_for_tokens("test_code", "test_state")
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self, oauth_service):
        """Test successful user info retrieval."""
        mock_id_info = {
            "sub": "123456789",
            "email": "test@example.com",
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg"
        }
        
        with patch('src.backend.services.oauth_service.id_token.verify_oauth2_token') as mock_verify:
            mock_verify.return_value = mock_id_info
            
            user_info = await oauth_service.get_user_info("test_access_token")
            
            assert isinstance(user_info, GoogleUserInfo)
            assert user_info.sub == "123456789"
            assert user_info.email == "test@example.com"
            assert user_info.email_verified is True
            assert user_info.name == "Test User"
            assert user_info.picture == "https://example.com/avatar.jpg"
    
    @pytest.mark.asyncio
    async def test_get_user_info_google_auth_error(self, oauth_service):
        """Test user info retrieval with Google auth error."""
        with patch('src.backend.services.oauth_service.id_token.verify_oauth2_token') as mock_verify:
            mock_verify.side_effect = GoogleAuthError("Invalid token")
            
            with pytest.raises(OAuthError, match="Invalid or expired access token"):
                await oauth_service.get_user_info("invalid_token")
    
    @pytest.mark.asyncio
    async def test_get_user_info_general_error(self, oauth_service):
        """Test user info retrieval with general error."""
        with patch('src.backend.services.oauth_service.id_token.verify_oauth2_token') as mock_verify:
            mock_verify.side_effect = Exception("Network error")
            
            with pytest.raises(OAuthError, match="Failed to retrieve user information"):
                await oauth_service.get_user_info("test_token")
    
    def test_validate_state_parameter_success(self, oauth_service):
        """Test successful state parameter validation."""
        state = "test_state_123"
        is_valid = oauth_service.validate_state_parameter(state, state)
        assert is_valid is True
    
    def test_validate_state_parameter_mismatch(self, oauth_service):
        """Test state parameter validation mismatch."""
        is_valid = oauth_service.validate_state_parameter("state1", "state2")
        assert is_valid is False
    
    def test_validate_state_parameter_missing(self, oauth_service):
        """Test state parameter validation with missing parameters."""
        is_valid = oauth_service.validate_state_parameter("", "state2")
        assert is_valid is False
        
        is_valid = oauth_service.validate_state_parameter("state1", "")
        assert is_valid is False
        
        is_valid = oauth_service.validate_state_parameter("", "")
        assert is_valid is False
    
    def test_validate_state_parameter_none(self, oauth_service):
        """Test state parameter validation with None values."""
        is_valid = oauth_service.validate_state_parameter(None, "state2")
        assert is_valid is False
        
        is_valid = oauth_service.validate_state_parameter("state1", None)
        assert is_valid is False
