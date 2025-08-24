"""Test transaction service functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from ..services.transaction_service import TransactionServiceImpl
from ..repositories.transaction_repository import MongoDBTransactionRepository
from ..models.transaction import Transaction, TransactionCreate, TransactionResponse


class TestTransactionService:
    """Test transaction service business logic."""
    
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
    
    async def test_create_transaction_after_scan_invalid_inputs(self, transaction_service):
        """Test transaction creation with invalid inputs."""
        # Test empty user_id
        result = await transaction_service.create_transaction_after_scan("", "scan123", 100)
        assert result is None
        
        # Test empty scan_id
        result = await transaction_service.create_transaction_after_scan("user123", "", 100)
        assert result is None
        
        # Test negative points
        result = await transaction_service.create_transaction_after_scan("user123", "scan123", -50)
        assert result is None
    
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
    
    async def test_get_user_transactions_success(self, transaction_service, mock_repository):
        """Test successful retrieval of user transactions."""
        # Arrange
        user_id = str(ObjectId())
        limit = 10
        offset = 0
        
        # Mock repository response
        mock_transactions = [
            MagicMock(id=ObjectId(), user_id=ObjectId(), scan_id=ObjectId(), amount=100, created_at="2024-01-15T10:00:00Z"),
            MagicMock(id=ObjectId(), user_id=ObjectId(), scan_id=ObjectId(), amount=150, created_at="2024-01-15T11:00:00Z")
        ]
        mock_repository.get_transactions_by_user_id.return_value = mock_transactions
        
        # Act
        result = await transaction_service.get_user_transactions(user_id, limit, offset)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(t, TransactionResponse) for t in result)
        mock_repository.get_transactions_by_user_id.assert_called_once_with(user_id, limit, offset)
    
    async def test_get_user_transactions_invalid_limit_offset(self, transaction_service, mock_repository):
        """Test transaction retrieval with invalid limit/offset values."""
        # Arrange
        user_id = str(ObjectId())
        
        # Mock repository response
        mock_repository.get_transactions_by_user_id.return_value = []
        
        # Act - Test invalid limit
        result = await transaction_service.get_user_transactions(user_id, limit=-5, offset=0)
        
        # Assert - Should use default limit of 20
        mock_repository.get_transactions_by_user_id.assert_called_with(user_id, 20, 0)
        
        # Act - Test invalid offset
        result = await transaction_service.get_user_transactions(user_id, limit=10, offset=-10)
        
        # Assert - Should use default offset of 0
        mock_repository.get_transactions_by_user_id.assert_called_with(user_id, 10, 0)
    
    async def test_get_user_transaction_summary_success(self, transaction_service, mock_repository):
        """Test successful retrieval of user transaction summary."""
        # Arrange
        user_id = str(ObjectId())
        mock_summary = {
            "total_transactions": 5,
            "total_points": 500,
            "average_points": 100.0
        }
        mock_repository.get_user_transaction_summary.return_value = mock_summary
        
        # Act
        result = await transaction_service.get_user_transaction_summary(user_id)
        
        # Assert
        assert result == mock_summary
        mock_repository.get_user_transaction_summary.assert_called_once_with(user_id)
    
    async def test_get_user_transaction_count_success(self, transaction_service, mock_repository):
        """Test successful retrieval of user transaction count."""
        # Arrange
        user_id = str(ObjectId())
        mock_count = 15
        mock_repository.get_user_transaction_count.return_value = mock_count
        
        # Act
        result = await transaction_service.get_user_transaction_count(user_id)
        
        # Assert
        assert result == mock_count
        mock_repository.get_user_transaction_count.assert_called_once_with(user_id)
