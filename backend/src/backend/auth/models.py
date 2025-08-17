"""Authentication domain models for SmartBin backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class OAuthToken(BaseModel):
    """OAuth token model for Google authentication."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GoogleUserInfo(BaseModel):
    """Google user information from OAuth."""

    sub: str  # Google user ID
    email: str
    email_verified: bool
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None


class JWTPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # User ID
    email: str
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    token_type: str = "access"  # access or refresh


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds
    user_id: str
    email: str
    name: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request model for logout."""

    refresh_token: str
