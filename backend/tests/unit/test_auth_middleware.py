"""Tests for authentication middleware."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer

from src.backend.middleware.auth_middleware import (
    AuthMiddleware,
    get_current_user,
    get_optional_user,
    is_authenticated,
    get_user_id,
    get_user_email
)
from src.backend.auth.models import JWTPayload
from src.backend.models.user import User


@pytest.fixture
def app():
    """Create a test FastAPI app with auth middleware."""
    app = FastAPI()
    
    @app.get("/protected")
    async def protected_endpoint(request: Request):
        return {"message": "Protected", "user": request.state.user.email}
    
    @app.get("/public")
    async def public_endpoint():
        return {"message": "Public"}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        id="test_user_123",
        email="test@example.com",
        name="Test User",
        points=100,
        google_id="google_123"
    )


@pytest.fixture
def mock_jwt_payload():
    """Create a mock JWT payload for testing."""
    return JWTPayload(
        sub="test_user_123",
        email="test@example.com",
        exp=9999999999,  # Far future
        iat=1234567890,
        token_type="access"
    )


class TestAuthMiddleware:
    """Test cases for AuthMiddleware class."""
    
    def test_middleware_initialization(self):
        """Test middleware initialization with default exclude paths."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        assert middleware.exclude_paths == [
            "/docs", "/redoc", "/openapi.json", "/health",
            "/auth/health", "/auth/google", "/auth/google/callback", "/auth/refresh"
        ]
    
    def test_middleware_initialization_custom_exclude_paths(self):
        """Test middleware initialization with custom exclude paths."""
        app = FastAPI()
        custom_paths = ["/custom", "/test"]
        middleware = AuthMiddleware(app, exclude_paths=custom_paths)
        
        assert middleware.exclude_paths == custom_paths
    
    def test_should_exclude_path(self):
        """Test path exclusion logic."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Test excluded paths
        assert middleware._should_exclude_path("/docs") is True
        assert middleware._should_exclude_path("/auth/google") is True
        assert middleware._should_exclude_path("/health") is True
        
        # Test non-excluded paths
        assert middleware._should_exclude_path("/scan") is False
        assert middleware._should_exclude_path("/user/profile") is False
        assert middleware._should_exclude_path("/api/v1/scan") is False
    
    def test_extract_token_from_authorization_header(self):
        """Test token extraction from Authorization header."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Mock request with Authorization header
        request = MagicMock()
        request.headers = {"Authorization": "Bearer test_token_123"}
        
        token = middleware._extract_token(request)
        assert token == "test_token_123"
    
    def test_extract_token_from_query_params(self):
        """Test token extraction from query parameters."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Mock request with token query parameter
        request = MagicMock()
        request.query_params = {"token": "query_token_123"}
        
        token = middleware._extract_token(request)
        assert token == "query_token_123"
    
    def test_extract_token_no_token(self):
        """Test token extraction when no token is present."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Mock request with no token
        request = MagicMock()
        request.headers = {}
        request.query_params = {}
        
        token = middleware._extract_token(request)
        assert token is None
    
    @patch('src.backend.services.service_factory.get_auth_service')
    @patch('src.backend.services.service_factory.get_user_service')
    async def test_authenticate_request_success(self, mock_get_user_service, mock_get_auth_service, mock_user, mock_jwt_payload):
        """Test successful request authentication."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Mock services
        mock_auth_service = MagicMock()
        mock_auth_service.verify_token.return_value = mock_jwt_payload
        mock_get_auth_service.return_value = mock_auth_service
        
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id.return_value = mock_user
        mock_get_user_service.return_value = mock_user_service
        
        # Mock request
        request = MagicMock()
        request.headers = {"Authorization": "Bearer valid_token"}
        
        # Test authentication
        user = await middleware._authenticate_request(request)
        
        assert user == mock_user
        mock_auth_service.verify_token.assert_called_once_with("valid_token", "access")
        mock_user_service.get_user_by_id.assert_called_once_with("test_user_123")
    
    @patch('src.backend.services.service_factory.get_auth_service')
    async def test_authenticate_request_missing_token(self, mock_get_auth_service):
        """Test authentication with missing token."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Mock request with no token
        request = MagicMock()
        request.headers = {}
        request.query_params = {}
        
        # Test authentication failure
        with pytest.raises(HTTPException) as exc_info:
            await middleware._authenticate_request(request)
        
        assert exc_info.value.status_code == 401
        assert "Missing authentication token" in str(exc_info.value.detail)
    
    @patch('src.backend.services.service_factory.get_auth_service')
    async def test_authenticate_request_expired_token(self, mock_get_auth_service):
        """Test authentication with expired token."""
        app = FastAPI()
        middleware = AuthMiddleware(app)
        
        # Mock auth service to raise TokenExpiredError
        mock_auth_service = MagicMock()
        from src.backend.auth.exceptions import TokenExpiredError
        mock_auth_service.verify_token.side_effect = TokenExpiredError("Token expired")
        mock_get_auth_service.return_value = mock_auth_service
        
        # Mock request
        request = MagicMock()
        request.headers = {"Authorization": "Bearer expired_token"}
        
        # Test authentication failure
        with pytest.raises(HTTPException) as exc_info:
            await middleware._authenticate_request(request)
        
        assert exc_info.value.status_code == 401
        assert "Token has expired" in str(exc_info.value.detail)


class TestAuthDependencies:
    """Test cases for authentication dependency functions."""
    
    def test_get_current_user_success(self, mock_user):
        """Test successful user retrieval from request state."""
        request = MagicMock()
        request.state.user = mock_user
        request.state.authenticated = True
        
        user = get_current_user(request)
        assert user == mock_user
    
    def test_get_current_user_not_authenticated(self):
        """Test user retrieval when not authenticated."""
        request = MagicMock()
        request.state.authenticated = False
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    def test_get_current_user_no_user_state(self):
        """Test user retrieval when no user state exists."""
        request = MagicMock()
        # No user state attributes
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    def test_get_optional_user_authenticated(self, mock_user):
        """Test optional user retrieval when authenticated."""
        request = MagicMock()
        request.state.user = mock_user
        request.state.authenticated = True
        
        user = get_optional_user(request)
        assert user == mock_user
    
    def test_get_optional_user_not_authenticated(self):
        """Test optional user retrieval when not authenticated."""
        request = MagicMock()
        request.state.authenticated = False
        
        user = get_optional_user(request)
        assert user is None
    
    def test_is_authenticated_true(self):
        """Test authentication check when authenticated."""
        request = MagicMock()
        request.state.authenticated = True
        
        result = is_authenticated(request)
        assert result is True
    
    def test_is_authenticated_false(self):
        """Test authentication check when not authenticated."""
        request = MagicMock()
        request.state.authenticated = False
        
        result = is_authenticated(request)
        assert result is False
    
    def test_get_user_id_authenticated(self, mock_user):
        """Test user ID retrieval when authenticated."""
        request = MagicMock()
        request.state.user = mock_user
        request.state.authenticated = True
        
        user_id = get_user_id(request)
        assert user_id == "test_user_123"
    
    def test_get_user_id_not_authenticated(self):
        """Test user ID retrieval when not authenticated."""
        request = MagicMock()
        request.state.authenticated = False
        
        user_id = get_user_id(request)
        assert user_id is None
    
    def test_get_user_email_authenticated(self, mock_user):
        """Test user email retrieval when authenticated."""
        request = MagicMock()
        request.state.user = mock_user
        request.state.authenticated = True
        
        email = get_user_email(request)
        assert email == "test@example.com"
    
    def test_get_user_email_not_authenticated(self):
        """Test user email retrieval when not authenticated."""
        request = MagicMock()
        request.state.authenticated = False
        
        email = get_user_email(request)
        assert email is None


class TestAuthMiddlewareIntegration:
    """Integration tests for authentication middleware."""
    
    @patch('src.backend.services.service_factory.get_auth_service')
    @patch('src.backend.services.service_factory.get_user_service')
    def test_protected_endpoint_with_valid_token(self, mock_get_user_service, mock_get_auth_service, mock_user, mock_jwt_payload):
        """Test protected endpoint access with valid token."""
        app = FastAPI()
        
        # Mock services
        mock_auth_service = MagicMock()
        mock_auth_service.verify_token.return_value = mock_jwt_payload
        mock_get_auth_service.return_value = mock_auth_service
        
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id.return_value = mock_user
        mock_get_user_service.return_value = mock_user_service
        
        # Add middleware
        app.add_middleware(AuthMiddleware)
        
        @app.get("/protected")
        async def protected_endpoint(request: Request):
            return {"user": request.state.user.email}
        
        client = TestClient(app)
        
        # Test with valid token
        response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})
        assert response.status_code == 200
        assert response.json()["user"] == "test@example.com"
    
    def test_protected_endpoint_without_token(self):
        """Test protected endpoint access without token."""
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        
        @app.get("/protected")
        async def protected_endpoint(request: Request):
            return {"user": request.state.user.email}
        
        client = TestClient(app)
        
        # Test without token
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Missing authentication token" in response.json()["detail"]
    
    def test_public_endpoint_access(self):
        """Test public endpoint access (should not require authentication)."""
        app = FastAPI()
        app.add_middleware(AuthMiddleware)
        
        @app.get("/public")
        async def public_endpoint():
            return {"message": "Public"}
        
        client = TestClient(app)
        
        # Test public endpoint
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json()["message"] == "Public"
