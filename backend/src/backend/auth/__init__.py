"""Authentication package for SmartBin backend."""

from .models import (
    OAuthToken,
    GoogleUserInfo,
    JWTPayload,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest
)

from .schemas import (
    UserProfileResponse,
    AuthErrorResponse,
    OAuthInitiateResponse,
    OAuthCallbackRequest,
    OAuthCallbackError
)

from .exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    OAuthError,
    OAuthStateMismatchError,
    OAuthCodeExchangeError,
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidUserDataError
)

__all__ = [
    # Models
    "OAuthToken",
    "GoogleUserInfo", 
    "JWTPayload",
    "TokenResponse",
    "RefreshTokenRequest",
    "LogoutRequest",
    
    # Schemas
    "UserProfileResponse",
    "AuthErrorResponse",
    "OAuthInitiateResponse",
    "OAuthCallbackRequest",
    "OAuthCallbackError",
    
    # Exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "OAuthError",
    "OAuthStateMismatchError",
    "OAuthCodeExchangeError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "InvalidUserDataError"
]
