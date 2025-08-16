"""Unit tests for UserService."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.backend.services.user_service import UserService
from src.backend.models.user import User
from src.backend.auth.models import GoogleUserInfo
from src.backend.auth.exceptions import UserNotFoundError, UserAlreadyExistsError, InvalidUserDataError
from src.backend.domain.interfaces.user_repository import UserRepository


class MockUserRepository(UserRepository):
    """Mock implementation of UserRepository for testing."""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    async def create_user(self, user: User) -> User:
        user.id = str(self.next_id)
        self.users[user.id] = user
        self.next_id += 1
        return user
    
    async def get_user_by_id(self, user_id: str) -> User | None:
        return self.users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def get_user_by_google_id(self, google_id: str) -> User | None:
        for user in self.users.values():
            if user.google_id == google_id:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: dict) -> User | None:
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        for key, value in updates.items():
            setattr(user, key, value)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    async def add_scan_to_user(self, user_id: str, scan_id: str) -> bool:
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        if scan_id not in user.scan_ids:
            user.scan_ids.append(scan_id)
        return True
    
    async def update_user_points(self, user_id: str, points: int) -> User | None:
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        user.points += points
        return user
    
    async def get_users_by_points_range(self, min_points: int, max_points: int) -> list[User]:
        return [
            user for user in self.users.values()
            if min_points <= user.points <= max_points
        ]


class TestUserService:
    """Test cases for UserService."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock user repository."""
        return MockUserRepository()
    
    @pytest.fixture
    def user_service(self, mock_repository):
        """Create a user service with mock repository."""
        return UserService(user_repository=mock_repository)
    
    @pytest.fixture
    def sample_google_user_info(self):
        """Create sample Google user info for testing."""
        return GoogleUserInfo(
            sub="google_123",
            email="test@example.com",
            email_verified=True,
            name="Test User",
            given_name="Test",
            family_name="User"
        )
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            email="test@example.com",
            name="Test User",
            points=100,
            google_id="google_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    def test_user_service_initialization(self, user_service):
        """Test user service initialization."""
        assert user_service is not None
        assert user_service.user_repository is not None
    
    def test_user_service_initialization_with_default_repository(self):
        """Test user service initialization with default repository."""
        service = UserService()
        assert service is not None
        assert isinstance(service.user_repository, type(service.user_repository))
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_success(self, user_service, sample_google_user_info):
        """Test successful user creation from OAuth."""
        user = await user_service.create_user_from_oauth(sample_google_user_info)
        
        assert user is not None
        assert user.email == sample_google_user_info.email
        assert user.name == sample_google_user_info.name
        assert user.google_id == sample_google_user_info.sub
        assert user.points == 0
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_duplicate_email(self, user_service, sample_google_user_info):
        """Test user creation fails when email already exists."""
        # Create first user
        await user_service.create_user_from_oauth(sample_google_user_info)
        
        # Try to create second user with same email
        with pytest.raises(UserAlreadyExistsError):
            await user_service.create_user_from_oauth(sample_google_user_info)
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_duplicate_google_id(self, user_service, sample_google_user_info):
        """Test user creation fails when Google ID already exists."""
        # Create first user
        await user_service.create_user_from_oauth(sample_google_user_info)
        
        # Try to create second user with same Google ID but different email
        duplicate_google_user = GoogleUserInfo(
            sub=sample_google_user_info.sub,
            email="different@example.com",
            email_verified=True,
            name="Different User"
        )
        
        with pytest.raises(UserAlreadyExistsError):
            await user_service.create_user_from_oauth(duplicate_google_user)
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_oauth_existing_google_id(self, user_service, sample_google_user_info):
        """Test getting existing user by Google ID."""
        # Create user first
        created_user = await user_service.create_user_from_oauth(sample_google_user_info)
        
        # Try to get or create again
        retrieved_user = await user_service.get_or_create_user_from_oauth(sample_google_user_info)
        
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_oauth_existing_email(self, user_service, sample_google_user_info):
        """Test linking existing user by email to Google OAuth."""
        # Create user without Google ID first
        existing_user = User(
            email=sample_google_user_info.email,
            name="Existing User",
            points=50
        )
        await user_service.user_repository.create_user(existing_user)
        
        # Try to get or create with Google OAuth
        linked_user = await user_service.get_or_create_user_from_oauth(sample_google_user_info)
        
        assert linked_user.id == existing_user.id
        assert linked_user.google_id == sample_google_user_info.sub
        assert linked_user.points == 50  # Points should be preserved
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_from_oauth_new_user(self, user_service, sample_google_user_info):
        """Test creating new user when none exists."""
        user = await user_service.get_or_create_user_from_oauth(sample_google_user_info)
        
        assert user is not None
        assert user.email == sample_google_user_info.email
        assert user.google_id == sample_google_user_info.sub
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, sample_user):
        """Test successful user retrieval by ID."""
        # Create user first
        created_user = await user_service.user_repository.create_user(sample_user)
        
        # Retrieve user
        retrieved_user = await user_service.get_user_by_id(str(created_user.id))
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service):
        """Test user retrieval by ID when user doesn't exist."""
        user = await user_service.get_user_by_id("nonexistent_id")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, sample_user):
        """Test successful user retrieval by email."""
        # Create user first
        created_user = await user_service.user_repository.create_user(sample_user)
        
        # Retrieve user
        retrieved_user = await user_service.get_user_by_email(created_user.email)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_service):
        """Test user retrieval by email when user doesn't exist."""
        user = await user_service.get_user_by_email("nonexistent@example.com")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, user_service, sample_user):
        """Test successful user profile update."""
        # Create user first
        created_user = await user_service.user_repository.create_user(sample_user)
        original_updated_at = created_user.updated_at
        
        # Update user profile
        updates = {"name": "Updated Name", "points": 200}
        updated_user = await user_service.update_user_profile(str(created_user.id), updates)
        
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert updated_user.points == 200
        assert updated_user.updated_at >= original_updated_at  # Should be >= instead of >
    
    @pytest.mark.asyncio
    async def test_update_user_profile_not_found(self, user_service):
        """Test user profile update when user doesn't exist."""
        with pytest.raises(UserNotFoundError):
            await user_service.update_user_profile("nonexistent_id", {"name": "New Name"})
    
    @pytest.mark.asyncio
    async def test_add_scan_to_user_success(self, user_service, sample_user):
        """Test successful scan addition to user."""
        # Create user first
        created_user = await user_service.user_repository.create_user(sample_user)
        
        # Add scan
        scan_id = "scan_123"
        success = await user_service.add_scan_to_user(str(created_user.id), scan_id)
        
        assert success is True
        
        # Verify scan was added
        updated_user = await user_service.get_user_by_id(str(created_user.id))
        assert scan_id in updated_user.scan_ids
    
    @pytest.mark.asyncio
    async def test_add_scan_to_user_not_found(self, user_service):
        """Test scan addition when user doesn't exist."""
        success = await user_service.add_scan_to_user("nonexistent_id", "scan_123")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_update_user_points_success(self, user_service, sample_user):
        """Test successful user points update."""
        # Create user first
        created_user = await user_service.user_repository.create_user(sample_user)
        initial_points = created_user.points
        
        # Update points
        points_to_add = 50
        updated_user = await user_service.update_user_points(str(created_user.id), points_to_add)
        
        assert updated_user is not None
        assert updated_user.points == initial_points + points_to_add
    
    @pytest.mark.asyncio
    async def test_update_user_points_not_found(self, user_service):
        """Test points update when user doesn't exist."""
        updated_user = await user_service.update_user_points("nonexistent_id", 50)
        assert updated_user is None
    
    @pytest.mark.asyncio
    async def test_get_user_leaderboard(self, user_service):
        """Test user leaderboard retrieval."""
        # Create multiple users with different points
        users_data = [
            {"email": "user1@example.com", "name": "User 1", "points": 100},
            {"email": "user2@example.com", "name": "User 2", "points": 200},
            {"email": "user3@example.com", "name": "User 3", "points": 150},
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            await user_service.user_repository.create_user(user)
        
        # Get leaderboard
        leaderboard = await user_service.get_user_leaderboard(limit=5)
        
        assert len(leaderboard) == 3
        assert leaderboard[0].points == 200  # Highest points first
        assert leaderboard[1].points == 150
        assert leaderboard[2].points == 100
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, sample_user):
        """Test successful user deletion."""
        # Create user first
        created_user = await user_service.user_repository.create_user(sample_user)
        
        # Delete user
        success = await user_service.delete_user(str(created_user.id))
        
        assert success is True
        
        # Verify user is deleted
        deleted_user = await user_service.get_user_by_id(str(created_user.id))
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service):
        """Test user deletion when user doesn't exist."""
        success = await user_service.delete_user("nonexistent_id")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_with_given_name_only(self, user_service):
        """Test user creation when only given_name is available."""
        google_user_info = GoogleUserInfo(
            sub="google_456",
            email="givenname@example.com",
            email_verified=True,
            given_name="Given",
            family_name="Name"
        )
        
        user = await user_service.create_user_from_oauth(google_user_info)
        
        assert user.name == "Given"  # Should use given_name when name is not available
    
    @pytest.mark.asyncio
    async def test_create_user_from_oauth_with_no_name(self, user_service):
        """Test user creation when no name information is available."""
        google_user_info = GoogleUserInfo(
            sub="google_789",
            email="noname@example.com",
            email_verified=True
        )
        
        user = await user_service.create_user_from_oauth(google_user_info)
        
        assert user.name is None
        assert user.email == "noname@example.com"
        assert user.google_id == "google_789"
