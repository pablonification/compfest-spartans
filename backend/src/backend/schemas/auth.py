from pydantic import BaseModel
from typing import Optional


class GoogleAuthResponse(BaseModel):
    """Response from Google OAuth2 flow"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    user: Optional['UserResponse'] = None


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: str
    name: Optional[str] = None
    points: int = 0


class LoginRequest(BaseModel):
    """Login request (if needed for future non-OAuth login)"""
    email: str
    password: str


# Update forward references
TokenResponse.model_rebuild()
UserResponse.model_rebuild()
