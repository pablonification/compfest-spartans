"""Unit tests for reward service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.backend.services.reward_service import add_points, get_user_points, get_user_stats
from src.backend.models.user import User
from src.backend.domain.interfaces import UserService


class TestRewardService:
    """Test cases for reward service."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        return User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=100,
            google_id="google_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scan_ids=["scan1", "scan2", "scan3"]
        )

    @pytest.fixture
    def mock_user_service(self):
        """Create a mock user service."""
        service = AsyncMock(spec=UserService)
        service.add_points.return_value = User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=150,  # 100 + 50
            google_id="google_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scan_ids=["scan1", "scan2", "scan3"]
        )
        service.get_user_by_id.return_value = User(
            id="test_user_id",
            email="test@example.com",
            name="Test User",
            points=150,
            google_id="google_123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            scan_ids=["scan1", "scan2", "scan3"]
        )
        return service

    @pytest.mark.asyncio
    async def test_add_points_success(self, mock_user, mock_user_service):
        """Test successful points addition."""
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await add_points(mock_user, 50)
            
            assert result == 150
            mock_user_service.add_points.assert_called_once_with("test_user_id", 50)

    @pytest.mark.asyncio
    async def test_add_points_failure_returns_current_points(self, mock_user, mock_user_service):
        """Test that current points are returned when points addition fails."""
        mock_user_service.add_points.side_effect = Exception("Database error")
        
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await add_points(mock_user, 50)
            
            assert result == 100  # Current user points
            mock_user_service.add_points.assert_called_once_with("test_user_id", 50)

    @pytest.mark.asyncio
    async def test_get_user_points_success(self, mock_user, mock_user_service):
        """Test successful user points retrieval."""
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_points(mock_user)
            
            assert result == 150
            mock_user_service.get_user_by_id.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_get_user_points_failure_returns_current_points(self, mock_user, mock_user_service):
        """Test that current points are returned when retrieval fails."""
        mock_user_service.get_user_by_id.side_effect = Exception("Database error")
        
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_points(mock_user)
            
            assert result == 100  # Current user points
            mock_user_service.get_user_by_id.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_get_user_points_user_not_found(self, mock_user, mock_user_service):
        """Test points retrieval when user is not found."""
        mock_user_service.get_user_by_id.return_value = None
        
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_points(mock_user)
            
            assert result == 100  # Current user points
            mock_user_service.get_user_by_id.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_get_user_stats_success(self, mock_user, mock_user_service):
        """Test successful user statistics retrieval."""
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_stats(mock_user)
            
            expected_stats = {
                "email": "test@example.com",
                "points": 150,
                "scan_count": 3,
                "total_rewards": 150,
                "created_at": mock_user.created_at,
                "last_login": mock_user.last_login
            }
            
            assert result == expected_stats
            mock_user_service.get_user_by_id.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_get_user_stats_failure_returns_basic_stats(self, mock_user, mock_user_service):
        """Test that basic stats are returned when retrieval fails."""
        mock_user_service.get_user_by_id.side_effect = Exception("Database error")
        
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_stats(mock_user)
            
            expected_stats = {
                "email": "test@example.com",
                "points": 100,
                "scan_count": 0,
                "total_rewards": 0,
                "error": "Failed to retrieve statistics"
            }
            
            assert result == expected_stats
            mock_user_service.get_user_by_id.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_get_user_stats_user_not_found(self, mock_user, mock_user_service):
        """Test stats retrieval when user is not found."""
        mock_user_service.get_user_by_id.return_value = None
        
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_stats(mock_user)
            
            expected_stats = {
                "email": "test@example.com",
                "points": 100,
                "scan_count": 0,
                "total_rewards": 0
            }
            
            assert result == expected_stats
            mock_user_service.get_user_by_id.assert_called_once_with("test_user_id")

    @pytest.mark.asyncio
    async def test_add_points_with_zero_points(self, mock_user, mock_user_service):
        """Test adding zero points."""
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await add_points(mock_user, 0)
            
            assert result == 150
            mock_user_service.add_points.assert_called_once_with("test_user_id", 0)

    @pytest.mark.asyncio
    async def test_add_points_with_large_number(self, mock_user, mock_user_service):
        """Test adding a large number of points."""
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await add_points(mock_user, 1000)
            
            assert result == 150
            mock_user_service.add_points.assert_called_once_with("test_user_id", 1000)

    @pytest.mark.asyncio
    async def test_get_user_stats_with_empty_scan_ids(self, mock_user, mock_user_service):
        """Test stats retrieval for user with no scans."""
        mock_user.scan_ids = []
        
        with patch("src.backend.services.reward_service.get_user_service", return_value=mock_user_service):
            result = await get_user_stats(mock_user)
            
            expected_stats = {
                "email": "test@example.com",
                "points": 150,
                "scan_count": 0,
                "total_rewards": 150,
                "created_at": mock_user.created_at,
                "last_login": mock_user.last_login
            }
            
            assert result == expected_stats
