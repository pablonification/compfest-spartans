"""Authentication service interface for SmartBin backend."""

from __future__ import annotations

from typing import Protocol, Optional

from ...auth.models import JWTPayload, TokenResponse


class AuthService(Protocol):
    """Protocol interface for authentication operations."""
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create a JWT access token for a user."""
        ...
    
    def create_refresh_token(self, user_id: str, email: str) -> str:
        """Create a JWT refresh token for a user."""
        ...
    
    def create_token_pair(self, user_id: str, email: str, name: Optional[str] = None) -> TokenResponse:
        """Create both access and refresh tokens for a user."""
        ...
    
    def verify_token(self, token: str, token_type: str = "access") -> JWTPayload:
        """Verify and decode a JWT token."""
        ...
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Generate a new access token using a valid refresh token."""
        ...
    
    def extract_user_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from a JWT token."""
        ...
    
    def is_token_expired(self, token: str) -> bool:
        """Check if a JWT token has expired."""
        ...
