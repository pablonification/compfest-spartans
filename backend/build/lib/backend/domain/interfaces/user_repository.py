"""User repository interface for SmartBin backend."""

from __future__ import annotations

from typing import Optional, List, Protocol

from ...models.user import User


class UserRepository(Protocol):
    """Protocol interface for user data operations."""
    
    async def create_user(self, user: User) -> User:
        """Create a new user in the database."""
        ...
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by their ID."""
        ...
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        ...
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Retrieve a user by their Google OAuth ID."""
        ...
    
    async def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        """Update user information."""
        ...
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user from the database."""
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
