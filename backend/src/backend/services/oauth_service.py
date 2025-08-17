"""Google OAuth service for SmartBin backend."""

from __future__ import annotations

import logging
import secrets
from typing import Optional
from urllib.parse import urlencode

import google.auth.transport.requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import GoogleAuthError

from ..core.config import get_settings
from ..auth.models import OAuthToken, GoogleUserInfo
from ..auth.exceptions import OAuthError, OAuthCodeExchangeError

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Service for handling Google OAuth authentication flow."""
    
    def __init__(self):
        """Initialize the Google OAuth service."""
        self.settings = get_settings()
        self._flow: Optional[Flow] = None
        
        # Validate required configuration
        if not self.settings.GOOGLE_CLIENT_ID:
            logger.warning("Google OAuth not configured: missing GOOGLE_CLIENT_ID")
        if not self.settings.GOOGLE_CLIENT_SECRET:
            logger.warning("Google OAuth not configured: missing GOOGLE_CLIENT_SECRET")
    
    def _get_flow(self) -> Flow:
        """Get or create the OAuth flow instance."""
        if self._flow is None:
            # Create OAuth flow with PKCE for enhanced security
            self._flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.settings.GOOGLE_CLIENT_ID,
                        "client_secret": self.settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.settings.GOOGLE_REDIRECT_URI],
                        "scopes": ["openid", "email", "profile"]
                    }
                },
                scopes=["openid", "email", "profile"]
            )
            self._flow.redirect_uri = self.settings.GOOGLE_REDIRECT_URI
        
        return self._flow
    
    def generate_authorization_url(self) -> tuple[str, str]:
        """
        Generate Google OAuth authorization URL with state parameter for CSRF protection.
        
        Returns:
            tuple: (authorization_url, state_parameter)
        """
        try:
            flow = self._get_flow()
            
            # Generate secure random state parameter for CSRF protection
            state = secrets.token_urlsafe(32)
            
            # Generate authorization URL
            authorization_url, _ = flow.authorization_url(
                access_type='offline',  # Request refresh token
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Always show consent screen
            )
            
            logger.info("Generated OAuth authorization URL with state: %s", state[:8])
            return authorization_url, state
            
        except Exception as e:
            logger.error("Failed to generate authorization URL: %s", e)
            raise OAuthError("Failed to generate authorization URL") from e
    
    async def exchange_code_for_tokens(self, code: str, state: str) -> OAuthToken:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Google
            state: State parameter for CSRF protection
            
        Returns:
            OAuthToken: Token information
            
        Raises:
            OAuthCodeExchangeError: If token exchange fails
        """
        try:
            flow = self._get_flow()
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=code)
            
            # Extract token information
            credentials = flow.credentials
            
            oauth_token = OAuthToken(
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                expires_in=credentials.expiry.timestamp() if credentials.expiry else 3600,
                scope=" ".join(credentials.scopes) if credentials.scopes else "openid email profile"
            )
            
            logger.info("Successfully exchanged code for tokens")
            return oauth_token
            
        except Exception as e:
            logger.error("Failed to exchange code for tokens: %s", e)
            raise OAuthCodeExchangeError("Failed to exchange authorization code for tokens") from e
    
    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Retrieve user information from Google using access token.
        
        Args:
            access_token: Valid Google access token
            
        Returns:
            GoogleUserInfo: User information from Google
            
        Raises:
            OAuthError: If user info retrieval fails
        """
        try:
            # Verify the token and get user info
            id_info = id_token.verify_oauth2_token(
                access_token,
                google.auth.transport.requests.Request(),
                self.settings.GOOGLE_CLIENT_ID
            )
            
            # Create GoogleUserInfo from verified token data
            user_info = GoogleUserInfo(
                sub=id_info["sub"],
                email=id_info["email"],
                email_verified=id_info.get("email_verified", False),
                name=id_info.get("name"),
                given_name=id_info.get("given_name"),
                family_name=id_info.get("family_name"),
                picture=id_info.get("picture"),
                locale=id_info.get("locale")
            )
            
            logger.info("Successfully retrieved user info for: %s", user_info.email)
            return user_info
            
        except GoogleAuthError as e:
            logger.error("Google auth error while getting user info: %s", e)
            raise OAuthError("Invalid or expired access token") from e
        except Exception as e:
            logger.error("Failed to get user info: %s", e)
            raise OAuthError("Failed to retrieve user information") from e
    
    def validate_state_parameter(self, expected_state: str, received_state: str) -> bool:
        """
        Validate state parameter to prevent CSRF attacks.
        
        Args:
            expected_state: Original state parameter sent to client
            received_state: State parameter received from OAuth callback
            
        Returns:
            bool: True if states match, False otherwise
        """
        if not expected_state or not received_state:
            logger.warning("Missing state parameter in OAuth flow")
            return False
        
        is_valid = secrets.compare_digest(expected_state, received_state)
        
        if not is_valid:
            logger.warning("State parameter mismatch in OAuth flow")
        
        return is_valid
