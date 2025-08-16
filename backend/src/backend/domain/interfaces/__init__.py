"""Domain interfaces package for SmartBin backend."""

from .user_repository import UserRepository
from .auth_service import AuthService
from .oauth_service import OAuthService

__all__ = [
    "UserRepository",
    "AuthService", 
    "OAuthService"
]
