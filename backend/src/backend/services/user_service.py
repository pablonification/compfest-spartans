"""User service for SmartBin backend."""

from __future__ import annotations

import logging
from typing import Optional, List
from datetime import datetime, timezone

from ..domain.interfaces.user_repository import UserRepository
from ..repositories.user_repository import MongoDBUserRepository
from ..models.user import User
from ..auth.models import GoogleUserInfo
from ..auth.exceptions import UserNotFoundError, UserAlreadyExistsError, InvalidUserDataError

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user operations and business logic."""
    
    def __init__(self, user_repository: Optional[UserRepository] = None):
        """Initialize the user service with a repository."""
        self.user_repository = user_repository or MongoDBUserRepository()
    
    async def create_user_from_oauth(self, google_user_info: GoogleUserInfo) -> User:
        """
        Create a new user from Google OAuth information.
        
        Args:
            google_user_info: Google user information from OAuth
            
        Returns:
            User: Created user instance
            
        Raises:
            UserAlreadyExistsError: If user with this email already exists
            InvalidUserDataError: If user data is invalid
        """
        try:
            # Check if user already exists by email
            existing_user = await self.user_repository.get_user_by_email(google_user_info.email)
            if existing_user:
                logger.warning("User already exists with email: %s", google_user_info.email)
                raise UserAlreadyExistsError(f"User with email {google_user_info.email} already exists")
            
            # Check if user exists by Google ID
            existing_google_user = await self.user_repository.get_user_by_google_id(google_user_info.sub)
            if existing_google_user:
                logger.warning("User already exists with Google ID: %s", google_user_info.sub)
                raise UserAlreadyExistsError(f"User with Google ID {google_user_info.sub} already exists")
            
            # Create new user
            user = User(
                email=google_user_info.email,
                name=google_user_info.name or google_user_info.given_name,
                google_id=google_user_info.sub,
                points=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save user to database
            created_user = await self.user_repository.create_user(user)
            
            logger.info("Created new user from OAuth: %s (ID: %s)", created_user.email, created_user.id)
            return created_user
            
        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error("Failed to create user from OAuth: %s", e)
            raise InvalidUserDataError(f"Failed to create user: {e}") from e
    
    async def get_or_create_user_from_oauth(self, google_user_info: GoogleUserInfo) -> User:
        """
        Get existing user or create new one from Google OAuth information.
        
        Args:
            google_user_info: Google user information from OAuth
            
        Returns:
            User: User instance (existing or newly created)
        """
        try:
            # First try to find user by Google ID
            user = await self.user_repository.get_user_by_google_id(google_user_info.sub)
            if user:
                logger.info("Found existing user by Google ID: %s", user.email)
                return user
            
            # Then try to find by email
            user = await self.user_repository.get_user_by_email(google_user_info.email)
            if user:
                # Update existing user with Google ID
                updated_user = await self.user_repository.update_user(
                    str(user.id),
                    {
                        "google_id": google_user_info.sub,
                        "updated_at": datetime.now(timezone.utc)
                    }
                )
                if updated_user:
                    logger.info("Linked existing user to Google OAuth: %s", updated_user.email)
                    return updated_user
                return user
            
            # Create new user if none exists
            return await self.create_user_from_oauth(google_user_info)
            
        except Exception as e:
            logger.error("Failed to get or create user from OAuth: %s", e)
            raise InvalidUserDataError(f"Failed to get or create user: {e}") from e
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User: User instance if found, None otherwise
        """
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            if user:
                logger.debug("Retrieved user by ID: %s", user_id)
            else:
                logger.debug("User not found by ID: %s", user_id)
            return user
            
        except Exception as e:
            logger.error("Failed to get user by ID %s: %s", user_id, e)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: User's email address
            
        Returns:
            User: User instance if found, None otherwise
        """
        try:
            user = await self.user_repository.get_user_by_email(email)
            if user:
                logger.debug("Retrieved user by email: %s", email)
            else:
                logger.debug("User not found by email: %s", email)
            return user
            
        except Exception as e:
            logger.error("Failed to get user by email %s: %s", email, e)
            return None
    
    async def update_user_profile(self, user_id: str, updates: dict) -> Optional[User]:
        """
        Update user profile information.
        
        Args:
            user_id: User's unique identifier
            updates: Dictionary of fields to update
            
        Returns:
            User: Updated user instance if successful, None otherwise
            
        Raises:
            UserNotFoundError: If user is not found
        """
        try:
            # Verify user exists
            existing_user = await self.user_repository.get_user_by_id(user_id)
            if not existing_user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Add updated_at timestamp
            updates["updated_at"] = datetime.now(timezone.utc)
            
            # Update user
            updated_user = await self.user_repository.update_user(user_id, updates)
            
            if updated_user:
                logger.info("Updated user profile: %s", user_id)
                return updated_user
            
            return None
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to update user profile %s: %s", user_id, e)
            return None
    
    async def add_scan_to_user(self, user_id: str, scan_id: str) -> bool:
        """
        Add a scan ID to the user's scan history.
        
        Args:
            user_id: User's unique identifier
            scan_id: Scan ID to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Verify user exists
            existing_user = await self.user_repository.get_user_by_id(user_id)
            if not existing_user:
                logger.warning("Cannot add scan to non-existent user: %s", user_id)
                return False
            
            # Add scan to user
            success = await self.user_repository.add_scan_to_user(user_id, scan_id)
            
            if success:
                logger.info("Added scan %s to user %s", scan_id, user_id)
            else:
                logger.warning("Failed to add scan %s to user %s", scan_id, user_id)
            
            return success
            
        except Exception as e:
            logger.error("Failed to add scan %s to user %s: %s", scan_id, user_id, e)
            return False
    
    async def update_user_points(self, user_id: str, points: int) -> Optional[User]:
        """
        Update user's points balance.
        
        Args:
            user_id: User's unique identifier
            points: Points to add (can be negative)
            
        Returns:
            User: Updated user instance if successful, None otherwise
        """
        try:
            # Verify user exists
            existing_user = await self.user_repository.get_user_by_id(user_id)
            if not existing_user:
                logger.warning("Cannot update points for non-existent user: %s", user_id)
                return None
            
            # Update points
            updated_user = await self.user_repository.update_user_points(user_id, points)
            
            if updated_user:
                logger.info("Updated points for user %s: +%d (total: %d)", 
                          user_id, points, updated_user.points)
                return updated_user
            
            return None
            
        except Exception as e:
            logger.error("Failed to update points for user %s: %s", user_id, e)
            return None
    
    async def add_points(self, user_id: str, points: int) -> Optional[User]:
        """
        Add points to user's balance (positive only).
        
        Args:
            user_id: User's unique identifier
            points: Points to add (must be positive)
            
        Returns:
            User: Updated user instance if successful, None otherwise
            
        Raises:
            ValueError: If points is negative
        """
        if points < 0:
            raise ValueError("Points to add must be positive")
        
        try:
            # Verify user exists
            existing_user = await self.user_repository.get_user_by_id(user_id)
            if not existing_user:
                logger.warning("Cannot add points to non-existent user: %s", user_id)
                return None
            
            # Add points (this will increment the current balance)
            updated_user = await self.user_repository.update_user_points(user_id, points)
            
            if updated_user:
                logger.info("Added %d points to user %s. New total: %d", 
                          points, user_id, updated_user.points)
                return updated_user
            
            return None
            
        except Exception as e:
            logger.error("Failed to add points to user %s: %s", user_id, e)
            return None
    
    async def get_user_leaderboard(self, limit: int = 10) -> List[User]:
        """
        Get top users by points for leaderboard.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List[User]: List of top users sorted by points
        """
        try:
            # Get users with highest points
            users = await self.user_repository.get_users_by_points_range(0, 999999)
            
            # Sort by points descending and limit results
            sorted_users = sorted(users, key=lambda u: u.points, reverse=True)[:limit]
            
            logger.info("Retrieved leaderboard with %d users", len(sorted_users))
            return sorted_users
            
        except Exception as e:
            logger.error("Failed to get user leaderboard: %s", e)
            return []
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from the system.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Verify user exists
            existing_user = await self.user_repository.get_user_by_id(user_id)
            if not existing_user:
                logger.warning("Cannot delete non-existent user: %s", user_id)
                return False
            
            # Delete user
            success = await self.user_repository.delete_user(user_id)
            
            if success:
                logger.info("Deleted user: %s", user_id)
            else:
                logger.warning("Failed to delete user: %s", user_id)
            
            return success
            
        except Exception as e:
            logger.error("Failed to delete user %s: %s", user_id, e)
            return False
    
    async def update_user_last_login(self, user_id: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update last login timestamp
            updated_user = await self.user_repository.update_user(
                user_id, 
                {"last_login": datetime.now(timezone.utc)}
            )
            
            if updated_user:
                logger.info("Updated last login for user: %s", user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to update last login for user %s: %s", user_id, e)
            return False
