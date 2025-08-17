"""Service factory for SmartBin backend using Protocol-based interfaces."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ..domain.interfaces import UserRepository, AuthService, OAuthService
from ..repositories.user_repository import MongoDBUserRepository
from .auth_service import JWTAuthService
from .oauth_service import GoogleOAuthService

if TYPE_CHECKING:
    from .user_service import UserService


class ServiceFactory:
    """Factory for creating and managing service instances."""
    
    def __init__(self):
        """Initialize the service factory."""
        self._user_repository: Optional[UserRepository] = None
        self._auth_service: Optional[AuthService] = None
        self._oauth_service: Optional[OAuthService] = None
    
    @property
    def user_repository(self) -> UserRepository:
        """Get or create the user repository instance."""
        if self._user_repository is None:
            self._user_repository = MongoDBUserRepository()
        return self._user_repository
    
    @property
    def auth_service(self) -> AuthService:
        """Get or create the authentication service instance."""
        if self._auth_service is None:
            self._auth_service = JWTAuthService()
        return self._auth_service
    
    @property
    def oauth_service(self) -> OAuthService:
        """Get or create the OAuth service instance."""
        if self._oauth_service is None:
            self._oauth_service = GoogleOAuthService()
        return self._oauth_service
    
    def create_user_service(self) -> UserService:
        """Create a user service with the configured repository."""
        from .user_service import UserService
        return UserService(user_repository=self.user_repository)
    
    def reset_services(self) -> None:
        """Reset all service instances (useful for testing)."""
        self._user_repository = None
        self._auth_service = None
        self._oauth_service = None


# Global service factory instance
service_factory = ServiceFactory()


def get_user_repository() -> UserRepository:
    """Get the global user repository instance."""
    return service_factory.user_repository


def get_auth_service() -> AuthService:
    """Get the global authentication service instance."""
    return service_factory.auth_service


def get_oauth_service() -> OAuthService:
    """Get the global OAuth service instance."""
    return service_factory.oauth_service


def get_user_service() -> UserService:
    """Get the global user service instance."""
    return service_factory.create_user_service()
