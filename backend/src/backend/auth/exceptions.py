"""Authentication exceptions for SmartBin backend."""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Base authentication error."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error."""
    
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class TokenExpiredError(AuthenticationError):
    """Token expired error."""
    
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class InvalidTokenError(AuthenticationError):
    """Invalid token error."""
    
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class OAuthError(HTTPException):
    """OAuth-related error."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class OAuthStateMismatchError(OAuthError):
    """OAuth state mismatch error (CSRF protection)."""
    
    def __init__(self, detail: str = "OAuth state mismatch"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class OAuthCodeExchangeError(OAuthError):
    """OAuth code exchange error."""
    
    def __init__(self, detail: str = "Failed to exchange OAuth code"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class UserNotFoundError(HTTPException):
    """User not found error."""
    
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class UserAlreadyExistsError(HTTPException):
    """User already exists error."""
    
    def __init__(self, detail: str = "User already exists"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)
