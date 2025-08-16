"""Authentication middleware for SmartBin backend."""

from __future__ import annotations

import logging
from typing import Optional, Callable
from contextlib import asynccontextmanager

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from ..auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError
)
from ..auth.models import JWTPayload
from ..services.service_factory import get_auth_service, get_user_service
from ..domain.interfaces import AuthService, UserService
from ..models.user import User

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication and user context injection."""
    
    def __init__(self, app, exclude_paths: Optional[list[str]] = None):
        """Initialize the authentication middleware.
        
        Args:
            app: FastAPI application instance
            exclude_paths: List of paths to exclude from authentication
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/auth/health",
            "/auth/google",
            "/auth/google/callback",
            "/auth/refresh"
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Process the request through authentication middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response: HTTP response from the endpoint
            
        Raises:
            HTTPException: If authentication fails
        """
        # Check if path should be excluded from authentication
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        try:
            # Extract and validate JWT token
            user = await self._authenticate_request(request)
            
            # Inject user context into request state
            request.state.user = user
            request.state.authenticated = True
            
            logger.debug("User authenticated: %s", user.email)
            
            # Continue to the next middleware/endpoint
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (like 401 Unauthorized)
            raise
        except Exception as e:
            logger.error("Authentication middleware error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error"
            )
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if a path should be excluded from authentication.
        
        Args:
            path: Request path
            
        Returns:
            bool: True if path should be excluded
        """
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    async def _authenticate_request(self, request: Request) -> User:
        """Authenticate the request and return user information.
        
        Args:
            request: FastAPI request object
            
        Returns:
            User: Authenticated user instance
            
        Raises:
            HTTPException: If authentication fails
        """
        # Extract token from Authorization header
        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token"
            )
        
        try:
            # Get services
            auth_service: AuthService = get_auth_service()
            user_service: UserService = get_user_service()
            
            # Verify the token
            payload: JWTPayload = auth_service.verify_token(token, "access")
            
            # Get user information
            user = await user_service.get_user_by_id(payload.sub)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return user
            
        except TokenExpiredError as e:
            logger.warning("Token expired: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            ) from e
        except InvalidTokenError as e:
            logger.warning("Invalid token: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            ) from e
        except Exception as e:
            logger.error("Token verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            ) from e
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from the request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: JWT token if found, None otherwise
        """
        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        
        # Try to get token from query parameter (for WebSocket connections)
        token = request.query_params.get("token")
        if token:
            return token
        
        return None


# Dependency function for protected endpoints
async def get_current_user(request: Request) -> User:
    """Get the current authenticated user from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, "user") or not request.state.authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.user


# Dependency function for optional authentication
async def get_optional_user(request: Request) -> Optional[User]:
    """Get the current user if authenticated, None otherwise.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User: Current user if authenticated, None otherwise
    """
    if hasattr(request.state, "user") and request.state.authenticated:
        return request.state.user
    return None


# Context manager for temporary authentication bypass
@asynccontextmanager
async def bypass_auth(request: Request):
    """Temporarily bypass authentication for a request.
    
    Args:
        request: FastAPI request object
        
    Yields:
        None: Context for bypassing authentication
    """
    original_user = getattr(request.state, "user", None)
    original_authenticated = getattr(request.state, "authenticated", False)
    
    try:
        # Set bypass state
        request.state.user = None
        request.state.authenticated = False
        yield
    finally:
        # Restore original state
        request.state.user = original_user
        request.state.authenticated = original_authenticated


# Utility function to check if user is authenticated
def is_authenticated(request: Request) -> bool:
    """Check if the current request is authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    return getattr(request.state, "authenticated", False)


# Utility function to get user ID from request
def get_user_id(request: Request) -> Optional[str]:
    """Get the current user ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: User ID if authenticated, None otherwise
    """
    if hasattr(request.state, "user") and request.state.user:
        return str(request.state.user.id)
    return None


# Utility function to get user email from request
def get_user_email(request: Request) -> Optional[str]:
    """Get the current user email from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: User email if authenticated, None otherwise
    """
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user.email
    return None
