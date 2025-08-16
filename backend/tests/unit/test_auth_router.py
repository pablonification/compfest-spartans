"""Tests for authentication router."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.backend.main import app
from src.backend.auth.models import OAuthInitiateResponse, TokenResponse


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestAuthRouter:
    """Test cases for authentication router endpoints."""
    
    def test_auth_health_check(self, client):
        """Test the authentication health check endpoint."""
        response = client.get("/auth/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "authentication"}
    
    @patch('src.backend.services.service_factory.get_oauth_service')
    def test_initiate_google_oauth_success(self, mock_get_oauth_service, client):
        """Test successful OAuth initiation."""
        # Mock the OAuth service
        mock_oauth_service = MagicMock()
        mock_oauth_service.generate_authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?client_id=test&scope=openid%20email%20profile",
            "test_state_123"
        )
        mock_get_oauth_service.return_value = mock_oauth_service
        
        response = client.get("/auth/google")
        assert response.status_code == 200
        
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert data["state"] == "test_state_123"
        assert "accounts.google.com" in data["authorization_url"]
    
    @patch('src.backend.services.service_factory.get_oauth_service')
    def test_initiate_google_oauth_service_unavailable(self, mock_get_oauth_service, client):
        """Test OAuth initiation when service is unavailable."""
        # Mock the OAuth service to raise an error
        mock_oauth_service = MagicMock()
        mock_oauth_service.generate_authorization_url.side_effect = Exception("Service unavailable")
        mock_get_oauth_service.return_value = mock_oauth_service
        
        response = client.get("/auth/google")
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_google_oauth_callback_missing_params(self, client):
        """Test OAuth callback with missing parameters."""
        response = client.get("/auth/google/callback")
        assert response.status_code == 422  # Validation error
    
    def test_refresh_token_missing_body(self, client):
        """Test token refresh with missing request body."""
        response = client.post("/auth/refresh")
        assert response.status_code == 422  # Validation error
    
    def test_logout_missing_body(self, client):
        """Test logout with missing request body."""
        response = client.post("/auth/logout")
        assert response.status_code == 422  # Validation error
    
    def test_user_profile_not_implemented(self, client):
        """Test user profile endpoint (currently not implemented)."""
        response = client.get("/auth/profile")
        assert response.status_code == 501
        assert "not implemented" in response.json()["detail"].lower()


class TestAuthRouterIntegration:
    """Integration tests for authentication router."""
    
    def test_auth_router_included_in_main_app(self, client):
        """Test that the auth router is properly included in the main app."""
        # Test that the auth router prefix is working
        response = client.get("/auth/health")
        assert response.status_code == 200
        
        # Test that the router is accessible
        response = client.get("/auth/google")
        # This might fail due to missing OAuth configuration, but the endpoint should exist
        assert response.status_code in [200, 503, 500]  # Various possible responses
    
    def test_auth_endpoints_accessible(self, client):
        """Test that all auth endpoints are accessible."""
        endpoints = [
            ("/auth/health", "GET"),
            ("/auth/google", "GET"),
            ("/auth/google/callback", "GET"),
            ("/auth/refresh", "POST"),
            ("/auth/logout", "POST"),
            ("/auth/profile", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            # All endpoints should be accessible (even if they return errors)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"
