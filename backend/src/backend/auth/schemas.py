"""Authentication API schemas for SmartBin backend."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


class UserProfileResponse(BaseModel):
    """User profile response schema."""

    id: str
    email: str
    name: Optional[str] = None
    points: int
    created_at: str


class AuthErrorResponse(BaseModel):
    """Authentication error response schema."""

    error: str
    error_description: Optional[str] = None
    error_code: Optional[str] = None


class OAuthInitiateResponse(BaseModel):
    """OAuth initiation response schema."""

    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request schema."""

    code: str
    state: str


class OAuthCallbackError(BaseModel):
    """OAuth callback error schema."""

    error: str
    error_description: Optional[str] = None
