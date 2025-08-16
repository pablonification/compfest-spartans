"""Authentication router for SmartBin backend."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse

from ..auth.schemas import (
    OAuthInitiateResponse,
    OAuthCallbackRequest,
    OAuthCallbackError,
    UserProfileResponse,
    AuthErrorResponse
)
from ..auth.models import TokenResponse, RefreshTokenRequest, LogoutRequest
from ..auth.exceptions import (
    OAuthError,
    OAuthCodeExchangeError,
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError
)
from ..services.service_factory import get_oauth_service, get_auth_service, get_user_service
from ..domain.interfaces import OAuthService, AuthService, UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/google", response_model=OAuthInitiateResponse)
async def initiate_google_oauth() -> OAuthInitiateResponse:
    """
    Initiate Google OAuth authentication flow.
    
    Returns:
        OAuthInitiateResponse: Authorization URL and state parameter
        
    Raises:
        HTTPException: If OAuth service is not configured
    """
    try:
        oauth_service: OAuthService = get_oauth_service()
        authorization_url, state = oauth_service.generate_authorization_url()
        
        logger.info("OAuth initiation successful for state: %s", state[:8])
        return OAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state
        )
        
    except OAuthError as e:
        logger.error("OAuth initiation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth service temporarily unavailable"
        ) from e
    except Exception as e:
        logger.error("Unexpected error during OAuth initiation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@router.get("/google/callback", response_model=TokenResponse)
async def google_oauth_callback(
    code: str,
    state: str,
    request: Request
) -> TokenResponse:
    """
    Handle Google OAuth callback and exchange code for tokens.
    
    Args:
        code: Authorization code from Google
        state: State parameter for CSRF protection
        request: FastAPI request object
        
    Returns:
        TokenResponse: JWT access and refresh tokens
        
    Raises:
        HTTPException: If OAuth callback fails
    """
    try:
        oauth_service: OAuthService = get_oauth_service()
        auth_service: AuthService = get_auth_service()
        user_service: UserService = get_user_service()
        
        # Exchange authorization code for OAuth tokens
        oauth_tokens = await oauth_service.exchange_code_for_tokens(code, state)
        
        # Get user information from Google
        google_user_info = await oauth_service.get_user_info(oauth_tokens.access_token)
        
        # Find or create user in our system
        user = await user_service.get_or_create_user_from_oauth(google_user_info)
        
        # Generate JWT tokens
        token_response = auth_service.create_token_pair(user.id, user.email, user.name)
        
        # Update user's last login
        await user_service.update_user_last_login(user.id)
        
        logger.info("OAuth callback successful for user: %s", user.email)
        
        # Set secure HTTP-only cookies for tokens
        response = TokenResponse(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            user_id=user.id,
            email=user.email,
            name=user.name
        )
        
        return response
        
    except OAuthCodeExchangeError as e:
        logger.error("OAuth code exchange failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code or state parameter"
        ) from e
    except OAuthError as e:
        logger.error("OAuth callback failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth service temporarily unavailable"
        ) from e
    except Exception as e:
        logger.error("Unexpected error during OAuth callback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest
) -> TokenResponse:
    """
    Refresh an expired access token using a valid refresh token.
    
    Args:
        refresh_request: Refresh token request containing the refresh token
        
    Returns:
        TokenResponse: New JWT access and refresh tokens
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        auth_service: AuthService = get_auth_service()
        user_service: UserService = get_user_service()
        
        # Verify the refresh token
        payload = auth_service.verify_token(refresh_request.refresh_token, "refresh")
        
        # Get user information
        user = await user_service.get_user_by_id(payload.sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate new token pair
        token_response = auth_service.create_token_pair(user.id, user.email, user.name)
        
        logger.info("Token refresh successful for user: %s", user.email)
        
        return TokenResponse(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            user_id=user.id,
            email=user.email,
            name=user.name
        )
        
    except TokenExpiredError as e:
        logger.warning("Refresh token expired: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        ) from e
    except InvalidTokenError as e:
        logger.warning("Invalid refresh token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        ) from e
    except Exception as e:
        logger.error("Unexpected error during token refresh: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(logout_request: LogoutRequest) -> dict[str, str]:
    """
    Logout user and invalidate refresh token.
    
    Args:
        logout_request: Logout request containing the refresh token
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If logout fails
    """
    try:
        auth_service: AuthService = get_auth_service()
        
        # Verify the refresh token to get user information
        payload = auth_service.verify_token(logout_request.refresh_token, "refresh")
        
        # Invalidate the refresh token (add to blacklist if implementing token blacklisting)
        # For now, we'll just log the logout
        logger.info("User logged out: %s", payload.email)
        
        # Return success message
        return {"message": "Successfully logged out"}
        
    except (InvalidTokenError, TokenExpiredError) as e:
        # Even if token is invalid, we consider logout successful
        logger.info("Logout with invalid/expired token: %s", e)
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error("Unexpected error during logout: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    request: Request
) -> UserProfileResponse:
    """
    Get current user's profile information.
    
    Args:
        request: FastAPI request object (will contain user context from middleware)
        
    Returns:
        UserProfileResponse: User profile information
        
    Raises:
        HTTPException: If user profile retrieval fails
    """
    try:
        # User context is injected by the auth middleware
        user = request.state.user
        
        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            points=user.points,
            created_at=user.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error("Unexpected error getting user profile: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e


@router.get("/health", status_code=status.HTTP_200_OK)
async def auth_health_check() -> dict[str, str]:
    """
    Health check endpoint for authentication service.
    
    Returns:
        dict: Health status
    """
    return {"status": "healthy", "service": "authentication"}
