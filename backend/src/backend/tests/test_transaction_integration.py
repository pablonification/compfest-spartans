"""Integration tests for complete transaction flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from ..services.transaction_service import TransactionServiceImpl
from ..repositories.transaction_repository import MongoDBTransactionRepository
from ..models.transaction import Transaction, TransactionCreate, TransactionResponse


class TestTransactionIntegration:
    """Test complete transaction flow integration."""
    
    @pytest.fixture
    def mock_mongo_db(self):
        """Create a mock MongoDB database."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.transactions = mock_collection
        return mock_db
    
    @pytest.fixture
    def transaction_repository(self, mock_mongo_db):
        """Create transaction repository with mock database."""
        with patch('src.backend.repositories.transaction_repository.mongo_db', mock_mongo_db):
            repo = MongoDBTransactionRepository()
            return repo
    
    @pytest.fixture
    def transaction_service(self, transaction_repository):
        """Create transaction service with mock repository."""
        return TransactionServiceImpl(transaction_repository)
    
    @pytest.fixture
    def sample_scan_data(self):
        """Sample scan data for testing."""
        return {
            "user_email": "user@example.com",
            "points_awarded": 150,
            "scan_id": str(ObjectId()),
            "timestamp": datetime.now(timezone.utc)
        }
    
    async def test_complete_transaction_flow(self, transaction_service, transaction_repository, sample_scan_data):
        """Test complete flow: scan -> transaction creation -> retrieval."""
        # Arrange
        user_id = sample_scan_data["user_email"]
        scan_id = sample_scan_data["scan_id"]
        points = sample_scan_data["points_awarded"]
        
        # Mock the MongoDB collection
        mock_collection = transaction_repository._get_collection()
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_insert_result
        
        # Act 1: Create transaction after scan
        created_transaction = await transaction_service.create_transaction_after_scan(
            user_id=user_id,
            scan_id=scan_id,
            points_awarded=points
        )
        
        # Assert 1: Transaction created successfully
        assert created_transaction is not None
        assert created_transaction.id == mock_insert_result.inserted_id
        assert created_transaction.user_id == ObjectId(user_id)
        assert created_transaction.scan_id == ObjectId(scan_id)
        assert created_transaction.amount == points
        
        # Act 2: Retrieve transaction by scan ID
        retrieved_transaction = await transaction_service.get_transaction_by_scan_id(scan_id)
        
        # Assert 2: Transaction retrieved successfully
        assert retrieved_transaction is not None
        assert retrieved_transaction.id == str(created_transaction.id)
        assert retrieved_transaction.user_id == user_id
        assert retrieved_transaction.scan_id == scan_id
        assert retrieved_transaction.amount == points
        
        # Act 3: Get user transaction summary
        summary = await transaction_service.get_user_transaction_summary(user_id)
        
        # Assert 3: Summary calculated correctly
        assert summary["total_transactions"] == 1
        assert summary["total_points"] == points
        assert summary["average_points"] == points
    
    async def test_transaction_creation_with_invalid_data(self, transaction_service):
        """Test transaction creation with invalid data."""
        # Test with empty user_id
        result = await transaction_service.create_transaction_after_scan("", "scan123", 100)
        assert result is None
        
        # Test with empty scan_id
        result = await transaction_service.create_transaction_after_scan("user123", "", 100)
        assert result is None
        
        # Test with negative points
        result = await transaction_service.create_transaction_after_scan("user123", "scan123", -50)
        assert result is None
    
    async def test_transaction_retrieval_pagination(self, transaction_service, transaction_repository):
        """Test transaction retrieval with pagination."""
        # Arrange
        user_id = "user@example.com"
        mock_collection = transaction_repository._get_collection()
        
        # Mock multiple transactions
        mock_transactions = [
            {
                "_id": ObjectId(),
                "user_id": ObjectId(user_id),
                "scan_id": ObjectId(),
                "amount": 100,
                "created_at": datetime.now(timezone.utc)
            },
            {
                "_id": ObjectId(),
                "user_id": ObjectId(user_id),
                "scan_id": ObjectId(),
                "amount": 150,
                "created_at": datetime.now(timezone.utc)
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: iter(mock_transactions)
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        
        # Act
        transactions = await transaction_service.get_user_transactions(user_id, limit=2, offset=0)
        
        # Assert
        assert len(transactions) == 2
        assert all(isinstance(t, TransactionResponse) for t in transactions)
    
    async def test_transaction_error_handling(self, transaction_service, transaction_repository):
        """Test error handling in transaction operations."""
        # Arrange
        user_id = "user@example.com"
        scan_id = "scan123"
        mock_collection = transaction_repository._get_collection()
        
        # Mock database error
        mock_collection.insert_one.side_effect = Exception("Database connection failed")
        
        # Act
        result = await transaction_service.create_transaction_after_scan(
            user_id=user_id,
            scan_id=scan_id,
            points_awarded=100
        )
        
        # Assert
        assert result is None  # Should handle error gracefully
    
    async def test_transaction_data_consistency(self, transaction_service, transaction_repository):
        """Test that transaction data remains consistent across operations."""
        # Arrange
        user_id = "user@example.com"
        scan_id = str(ObjectId())
        points = 200
        
        # Mock successful insertion
        mock_collection = transaction_repository._get_collection()
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_insert_result
        
        # Act 1: Create transaction
        created_transaction = await transaction_service.create_transaction_after_scan(
            user_id=user_id,
            scan_id=scan_id,
            points_awarded=points
        )
        
        # Assert 1: Transaction created with correct data
        assert created_transaction.user_id == ObjectId(user_id)
        assert created_transaction.scan_id == ObjectId(scan_id)
        assert created_transaction.amount == points
        
        # Act 2: Retrieve transaction
        retrieved_transaction = await transaction_service.get_transaction_by_scan_id(scan_id)
        
        # Assert 2: Retrieved data matches created data
        assert retrieved_transaction.user_id == user_id  # Converted back to string
        assert retrieved_transaction.scan_id == scan_id  # Converted back to string
        assert retrieved_transaction.amount == points
    
    async def test_transaction_summary_calculation(self, transaction_service, transaction_repository):
        """Test transaction summary calculation accuracy."""
        # Arrange
        user_id = "user@example.com"
        mock_collection = transaction_repository._get_collection()
        
        # Mock aggregation pipeline result
        mock_summary = {
            "total_transactions": 3,
            "total_points": 450,
            "average_points": 150.0
        }
        
        mock_aggregate_result = [mock_summary]
        mock_collection.aggregate.return_value.to_list.return_value = mock_aggregate_result
        
        # Act
        summary = await transaction_service.get_user_transaction_summary(user_id)
        
        # Assert
        assert summary["total_transactions"] == 3
        assert summary["total_points"] == 450
        assert summary["average_points"] == 150.0
        
        # Verify aggregation pipeline was called correctly
        mock_collection.aggregate.assert_called_once()
        pipeline = mock_collection.aggregate.call_args[0][0]
        assert len(pipeline) == 2  # Match and group stages
        assert pipeline[0]["$match"]["user_id"] == ObjectId(user_id)
