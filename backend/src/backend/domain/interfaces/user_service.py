"""User service interface for SmartBin backend."""

from __future__ import annotations

from typing import Protocol, Optional, List

from ...models.user import User
from ...auth.models import GoogleUserInfo


class UserService(Protocol):
    """Protocol interface for user operations."""
    
    async def create_user_from_oauth(self, google_user_info: GoogleUserInfo) -> User:
        """Create a new user from Google OAuth information."""
        ...
    
    async def get_or_create_user_from_oauth(self, google_user_info: GoogleUserInfo) -> User:
        """Get existing user or create new one from Google OAuth information."""
        ...
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        ...
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        ...
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google OAuth ID."""
        ...
    
    async def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user information."""
        ...
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        ...
    
    async def add_scan_to_user(self, user_id: str, scan_id: str) -> bool:
        """Add a scan ID to the user's scan history."""
        ...
    
    async def update_user_points(self, user_id: str, points: int) -> Optional[User]:
        """Update user's points balance."""
        ...
    
    async def get_users_by_points_range(self, min_points: int, max_points: int) -> List[User]:
        """Get users within a points range (for leaderboards)."""
        ...
    
    async def get_user_leaderboard(self, limit: int = 10) -> List[User]:
        """Get top users by points for leaderboard."""
        ...
    
    async def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        ...
