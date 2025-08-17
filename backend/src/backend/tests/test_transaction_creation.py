"""Test transaction creation functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from ..models.transaction import TransactionCreate
from ..services.transaction_service import TransactionServiceImpl
from ..repositories.transaction_repository import MongoDBTransactionRepository


class TestTransactionCreation:
    """Test transaction creation after scan."""
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock transaction repository."""
        mock_repo = AsyncMock(spec=MongoDBTransactionRepository)
        return mock_repo
    
    @pytest.fixture
    def transaction_service(self, mock_repository):
        """Create transaction service with mock repository."""
        return TransactionServiceImpl(mock_repository)
    
    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data for testing."""
        return {
            "user_id": str(ObjectId()),
            "scan_id": str(ObjectId()),
            "points_awarded": 100
        }
    
    @pytest.mark.asyncio
    async def test_create_transaction_after_scan_success(self, transaction_service, mock_repository, sample_transaction_data):
        """Test successful transaction creation after scan."""
        # Arrange
        user_id = sample_transaction_data["user_id"]
        scan_id = sample_transaction_data["scan_id"]
        points_awarded = sample_transaction_data["points_awarded"]
        
        # Mock successful transaction creation
        mock_transaction = MagicMock()
        mock_transaction.id = ObjectId()
        mock_repository.create_transaction.return_value = mock_transaction
        
        # Act
        result = await transaction_service.create_transaction_after_scan(
            user_id, scan_id, points_awarded
        )
        
        # Assert
        assert result is not None
        assert result.id == mock_transaction.id
        mock_repository.create_transaction.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_repository.create_transaction.call_args[0][0]
        assert isinstance(call_args, TransactionCreate)
        assert call_args.user_id == user_id
        assert call_args.scan_id == scan_id
        assert call_args.amount == points_awarded
    
    @pytest.mark.asyncio
    async def test_create_transaction_after_scan_invalid_inputs(self, transaction_service):
        """Test transaction creation with invalid inputs."""
        # Test with empty user_id
        result = await transaction_service.create_transaction_after_scan("", "scan123", 100)
        assert result is None
        
        # Test with empty scan_id
        result = await transaction_service.create_transaction_after_scan("user123", "", 100)
        assert result is None
        
        # Test with negative points
        result = await transaction_service.create_transaction_after_scan("user123", "scan123", -50)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_transaction_after_scan_repository_failure(self, transaction_service, mock_repository, sample_transaction_data):
        """Test transaction creation when repository fails."""
        # Arrange
        user_id = sample_transaction_data["user_id"]
        scan_id = sample_transaction_data["scan_id"]
        points_awarded = sample_transaction_data["points_awarded"]
        
        # Mock repository failure
        mock_repository.create_transaction.return_value = None
        
        # Act
        result = await transaction_service.create_transaction_after_scan(
            user_id, scan_id, points_awarded
        )
        
        # Assert
        assert result is None
        mock_repository.create_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_transaction_after_scan_exception_handling(self, transaction_service, mock_repository, sample_transaction_data):
        """Test transaction creation handles exceptions gracefully."""
        # Arrange
        user_id = sample_transaction_data["user_id"]
        scan_id = sample_transaction_data["scan_id"]
        points_awarded = sample_transaction_data["points_awarded"]
        
        # Mock repository exception
        mock_repository.create_transaction.side_effect = Exception("Database error")
        
        # Act
        result = await transaction_service.create_transaction_after_scan(
            user_id, scan_id, points_awarded
        )
        
        # Assert
        assert result is None
        mock_repository.create_transaction.assert_called_once()
