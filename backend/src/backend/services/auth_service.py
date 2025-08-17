"""JWT authentication service for SmartBin backend."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from jose import JWTError, jwt

from ..core.config import get_settings
from ..auth.models import JWTPayload, TokenResponse
from ..auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    InvalidCredentialsError
)

logger = logging.getLogger(__name__)


class JWTAuthService:
    """Service for handling JWT token operations."""
    
    def __init__(self):
        """Initialize the JWT authentication service."""
        self.settings = get_settings()
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate JWT configuration settings."""
        if not self.settings.JWT_SECRET_KEY or self.settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            logger.warning("JWT_SECRET_KEY not configured or using default value")
        
        if not self.settings.JWT_ALGORITHM:
            logger.warning("JWT_ALGORITHM not configured")
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            str: JWT access token
            
        Raises:
            AuthenticationError: If token creation fails
        """
        try:
            # Calculate expiration time
            expires_delta = timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.now(timezone.utc) + expires_delta
            
            # Create token payload
            payload = {
                "sub": user_id,
                "email": email,
                "exp": int(expire.timestamp()),
                "iat": int(datetime.now(timezone.utc).timestamp()),
                "token_type": "access"
            }
            
            # Generate JWT token
            token = jwt.encode(
                payload,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM
            )
            
            logger.info("Created access token for user: %s", email)
            return token
            
        except Exception as e:
            logger.error("Failed to create access token: %s", e)
            raise AuthenticationError("Failed to create access token") from e
    
    def create_refresh_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT refresh token for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            str: JWT refresh token
            
        Raises:
            AuthenticationError: If token creation fails
        """
        try:
            # Calculate expiration time
            expires_delta = timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
            expire = datetime.now(timezone.utc) + expires_delta
            
            # Create token payload
            payload = {
                "sub": user_id,
                "email": email,
                "exp": int(expire.timestamp()),
                "iat": int(datetime.now(timezone.utc).timestamp()),
                "token_type": "refresh"
            }
            
            # Generate JWT token
            token = jwt.encode(
                payload,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM
            )
            
            logger.info("Created refresh token for user: %s", email)
            return token
            
        except Exception as e:
            logger.error("Failed to create refresh token: %s", e)
            raise AuthenticationError("Failed to create refresh token") from e
    
    def create_token_pair(self, user_id: str, email: str, name: Optional[str] = None) -> TokenResponse:
        """
        Create both access and refresh tokens for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            name: User's display name (optional)
            
        Returns:
            TokenResponse: Complete token information
        """
        access_token = self.create_access_token(user_id, email)
        refresh_token = self.create_refresh_token(user_id, email)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user_id=user_id,
            email=email,
            name=name
        )
    
    def verify_token(self, token: str, token_type: str = "access") -> JWTPayload:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            JWTPayload: Decoded token payload
            
        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
            AuthenticationError: If token verification fails
        """
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            
            # Validate token type
            if payload.get("token_type") != token_type:
                logger.warning("Token type mismatch: expected %s, got %s", token_type, payload.get("token_type"))
                raise InvalidTokenError("Invalid token type")
            
            # Check if token has expired
            exp = payload.get("exp")
            if exp and datetime.now(timezone.utc).timestamp() > exp:
                logger.warning("Token expired for user: %s", payload.get("email"))
                raise TokenExpiredError("Token has expired")
            
            # Create JWTPayload object
            jwt_payload = JWTPayload(
                sub=payload["sub"],
                email=payload["email"],
                exp=payload["exp"],
                iat=payload["iat"],
                token_type=payload["token_type"]
            )
            
            logger.debug("Successfully verified %s token for user: %s", token_type, jwt_payload.email)
            return jwt_payload
            
        except JWTError as e:
            logger.warning("JWT decode error: %s", e)
            raise InvalidTokenError("Invalid token format") from e
        except (KeyError, ValueError) as e:
            logger.warning("Token payload validation error: %s", e)
            raise InvalidTokenError("Invalid token payload") from e
        except (InvalidTokenError, TokenExpiredError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error("Unexpected error during token verification: %s", e)
            raise AuthenticationError("Token verification failed") from e
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate a new access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            str: New access token
            
        Raises:
            InvalidTokenError: If refresh token is invalid
            TokenExpiredError: If refresh token has expired
            AuthenticationError: If token refresh fails
        """
        try:
            # Verify the refresh token
            payload = self.verify_token(refresh_token, "refresh")
            
            # Create new access token
            new_access_token = self.create_access_token(payload.sub, payload.email)
            
            logger.info("Refreshed access token for user: %s", payload.email)
            return new_access_token
            
        except (InvalidTokenError, TokenExpiredError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error("Failed to refresh access token: %s", e)
            raise AuthenticationError("Failed to refresh access token") from e
    
    def extract_user_from_token(self, token: str) -> tuple[str, str]:
        """
        Extract user ID and email from a valid access token.
        
        Args:
            token: Valid access token
            
        Returns:
            tuple: (user_id, email)
            
        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
        """
        payload = self.verify_token(token, "access")
        return payload.sub, payload.email
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without raising exceptions.
        
        Args:
            token: JWT token to check
            
        Returns:
            bool: True if token is expired, False otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            
            exp = payload.get("exp")
            if exp:
                return datetime.now(timezone.utc).timestamp() > exp
            
            return False
            
        except (JWTError, KeyError, ValueError):
            return True
