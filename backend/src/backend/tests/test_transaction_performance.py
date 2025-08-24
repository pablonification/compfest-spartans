"""Performance tests for transaction system."""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from ..services.transaction_service import TransactionServiceImpl
from ..repositories.transaction_repository import MongoDBTransactionRepository
from ..models.transaction import TransactionResponse


class TestTransactionPerformance:
    """Test transaction system performance under load."""
    
    @pytest.fixture
    def mock_mongo_db(self):
        """Create a mock MongoDB database for performance testing."""
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
    
    async def test_bulk_transaction_creation_performance(self, transaction_service, transaction_repository):
        """Test performance of creating multiple transactions."""
        # Arrange
        num_transactions = 100
        mock_collection = transaction_repository._get_collection()
        
        # Mock successful insertions
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_insert_result
        
        # Act
        start_time = time.time()
        
        # Create transactions concurrently
        tasks = []
        for i in range(num_transactions):
            task = transaction_service.create_transaction_after_scan(
                user_id=f"user{i}@example.com",
                scan_id=str(ObjectId()),
                points_awarded=100 + i
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert
        assert len(results) == num_transactions
        assert all(result is not None for result in results)
        
        # Performance assertion: should complete within reasonable time
        # 100 transactions should complete in under 1 second
        assert execution_time < 1.0
        
        # Verify all insertions were called
        assert mock_collection.insert_one.call_count == num_transactions
    
    async def test_transaction_retrieval_performance(self, transaction_service, transaction_repository):
        """Test performance of retrieving multiple transactions."""
        # Arrange
        user_id = "user@example.com"
        num_transactions = 50
        mock_collection = transaction_repository._get_collection()
        
        # Mock transaction data
        mock_transactions = []
        for i in range(num_transactions):
            mock_transactions.append({
                "_id": ObjectId(),
                "user_id": ObjectId(user_id),
                "scan_id": ObjectId(),
                "amount": 100 + i,
                "created_at": datetime.now(timezone.utc)
            })
        
        # Mock cursor for pagination
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: iter(mock_transactions)
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        
        # Act
        start_time = time.time()
        
        # Retrieve transactions with different pagination
        tasks = []
        for offset in range(0, num_transactions, 10):
            task = transaction_service.get_user_transactions(
                user_id=user_id,
                limit=10,
                offset=offset
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert
        assert len(results) == 5  # 50 transactions / 10 per page
        assert all(len(result) == 10 for result in results)
        
        # Performance assertion: should complete quickly
        assert execution_time < 0.5
    
    async def test_transaction_summary_performance(self, transaction_service, transaction_repository):
        """Test performance of transaction summary calculations."""
        # Arrange
        user_id = "user@example.com"
        mock_collection = transaction_repository._get_collection()
        
        # Mock aggregation result
        mock_summary = {
            "total_transactions": 1000,
            "total_points": 150000,
            "average_points": 150.0
        }
        mock_aggregate_result = [mock_summary]
        mock_collection.aggregate.return_value.to_list.return_value = mock_aggregate_result
        
        # Mock count operation
        mock_collection.count_documents.return_value = 1000
        
        # Act
        start_time = time.time()
        
        # Run multiple summary operations concurrently
        tasks = [
            transaction_service.get_user_transaction_summary(user_id),
            transaction_service.get_user_transaction_count(user_id),
            transaction_service.get_user_transaction_summary(user_id),  # Repeat to test caching
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert
        assert len(results) == 3
        assert all(result is not None for result in results)
        
        # Performance assertion: summary operations should be fast
        assert execution_time < 0.3
    
    async def test_concurrent_user_transactions(self, transaction_service, transaction_repository):
        """Test performance with multiple concurrent users."""
        # Arrange
        num_users = 20
        transactions_per_user = 10
        mock_collection = transaction_repository._get_collection()
        
        # Mock successful insertions
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = ObjectId()
        mock_collection.insert_one.return_value = mock_insert_result
        
        # Act
        start_time = time.time()
        
        # Simulate multiple users creating transactions simultaneously
        all_tasks = []
        for user_idx in range(num_users):
            user_id = f"user{user_idx}@example.com"
            for tx_idx in range(transactions_per_user):
                task = transaction_service.create_transaction_after_scan(
                    user_id=user_id,
                    scan_id=str(ObjectId()),
                    points_awarded=100 + tx_idx
                )
                all_tasks.append(task)
        
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert
        total_transactions = num_users * transactions_per_user
        assert len(results) == total_transactions
        assert all(result is not None for result in results)
        
        # Performance assertion: should handle concurrent users efficiently
        # 200 transactions should complete in under 2 seconds
        assert execution_time < 2.0
        
        # Verify all insertions were called
        assert mock_collection.insert_one.call_count == total_transactions
    
    async def test_memory_efficiency(self, transaction_service, transaction_repository):
        """Test memory efficiency with large result sets."""
        # Arrange
        user_id = "user@example.com"
        large_limit = 1000
        mock_collection = transaction_repository._get_collection()
        
        # Mock large transaction dataset
        mock_transactions = []
        for i in range(large_limit):
            mock_transactions.append({
                "_id": ObjectId(),
                "user_id": ObjectId(user_id),
                "scan_id": ObjectId(),
                "amount": 100 + i,
                "created_at": datetime.now(timezone.utc)
            })
        
        # Mock cursor for large dataset
        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = lambda self: iter(mock_transactions)
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        
        # Act
        start_time = time.time()
        
        # Retrieve large dataset
        transactions = await transaction_service.get_user_transactions(
            user_id=user_id,
            limit=large_limit,
            offset=0
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert
        assert len(transactions) == large_limit
        assert all(isinstance(t, TransactionResponse) for t in transactions)
        
        # Performance assertion: should handle large datasets efficiently
        assert execution_time < 1.0
        
        # Memory efficiency: should not cause excessive memory usage
        # This is more of a qualitative test - in real scenarios, we'd monitor memory usage
    
    async def test_error_handling_performance(self, transaction_service, transaction_repository):
        """Test that error handling doesn't significantly impact performance."""
        # Arrange
        user_id = "user@example.com"
        scan_id = "scan123"
        mock_collection = transaction_repository._get_collection()
        
        # Mock database errors
        mock_collection.insert_one.side_effect = Exception("Database error")
        
        # Act
        start_time = time.time()
        
        # Attempt to create transactions (will fail)
        tasks = []
        for i in range(50):
            task = transaction_service.create_transaction_after_scan(
                user_id=user_id,
                scan_id=f"{scan_id}_{i}",
                points_awarded=100
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert
        assert len(results) == 50
        assert all(result is None for result in results)  # All should fail gracefully
        
        # Performance assertion: error handling should be fast
        assert execution_time < 0.5
