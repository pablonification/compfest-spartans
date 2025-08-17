"""Middleware package for SmartBin backend."""

from .auth_middleware import (
    AuthMiddleware,
    get_current_user,
    get_optional_user,
    bypass_auth,
    is_authenticated,
    get_user_id,
    get_user_email
)

__all__ = [
    "AuthMiddleware",
    "get_current_user",
    "get_optional_user", 
    "bypass_auth",
    "is_authenticated",
    "get_user_id",
    "get_user_email"
]
