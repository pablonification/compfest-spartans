"""OAuth service interface for SmartBin backend."""

from __future__ import annotations

from typing import Protocol, Tuple

from ...auth.models import OAuthToken, GoogleUserInfo


class OAuthService(Protocol):
    """Protocol interface for OAuth operations."""
    
    def generate_authorization_url(self) -> Tuple[str, str]:
        """Generate OAuth authorization URL with state parameter."""
        ...
    
    async def exchange_code_for_tokens(self, code: str, state: str) -> OAuthToken:
        """Exchange authorization code for access and refresh tokens."""
        ...
    
    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Retrieve user information from OAuth provider."""
        ...
    
    def validate_state_parameter(self, received_state: str, expected_state: str) -> bool:
        """Validate OAuth state parameter for CSRF protection."""
        ...
