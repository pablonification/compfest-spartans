"""Test transaction models functionality."""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from ..models.transaction import Transaction, TransactionCreate, TransactionResponse


class TestTransactionModels:
    """Test transaction model validation and serialization."""
    
    def test_transaction_model_creation(self):
        """Test creating a Transaction model instance."""
        # Arrange
        user_id = ObjectId()
        scan_id = ObjectId()
        amount = 100
        created_at = datetime.now(timezone.utc)
        
        # Act
        transaction = Transaction(
            user_id=user_id,
            scan_id=scan_id,
            amount=amount,
            created_at=created_at
        )
        
        # Assert
        assert transaction.user_id == user_id
        assert transaction.scan_id == scan_id
        assert transaction.amount == amount
        assert transaction.created_at == created_at
        assert transaction.id is None  # Not set until saved to DB
    
    def test_transaction_create_model_validation(self):
        """Test TransactionCreate model validation."""
        # Arrange & Act
        transaction_create = TransactionCreate(
            user_id=str(ObjectId()),
            scan_id=str(ObjectId()),
            amount=150
        )
        
        # Assert
        assert transaction_create.user_id is not None
        assert transaction_create.scan_id is not None
        assert transaction_create.amount == 150
        assert transaction_create.created_at is not None
    
    def test_transaction_response_model_creation(self):
        """Test TransactionResponse model creation."""
        # Arrange
        transaction_id = str(ObjectId())
        user_id = str(ObjectId())
        scan_id = str(ObjectId())
        amount = 200
        created_at = "2024-01-15T10:30:00Z"
        
        # Act
        response = TransactionResponse(
            id=transaction_id,
            user_id=user_id,
            scan_id=scan_id,
            amount=amount,
            created_at=created_at
        )
        
        # Assert
        assert response.id == transaction_id
        assert response.user_id == user_id
        assert response.scan_id == scan_id
        assert response.amount == amount
        assert response.created_at == created_at
    
    def test_transaction_model_json_serialization(self):
        """Test that Transaction model can be serialized to JSON."""
        # Arrange
        user_id = ObjectId()
        scan_id = ObjectId()
        amount = 75
        created_at = datetime.now(timezone.utc)
        
        transaction = Transaction(
            user_id=user_id,
            scan_id=scan_id,
            amount=amount,
            created_at=created_at
        )
        
        # Act
        transaction_dict = transaction.model_dump()
        
        # Assert
        assert "user_id" in transaction_dict
        assert "scan_id" in transaction_dict
        assert "amount" in transaction_dict
        assert "created_at" in transaction_dict
        assert transaction_dict["amount"] == 75
    
    def test_transaction_create_model_json_serialization(self):
        """Test that TransactionCreate model can be serialized to JSON."""
        # Arrange
        transaction_create = TransactionCreate(
            user_id=str(ObjectId()),
            scan_id=str(ObjectId()),
            amount=300
        )
        
        # Act
        create_dict = transaction_create.model_dump()
        
        # Assert
        assert "user_id" in create_dict
        assert "scan_id" in create_dict
        assert "amount" in create_dict
        assert "created_at" in create_dict
        assert create_dict["amount"] == 300
    
    def test_transaction_response_model_json_serialization(self):
        """Test that TransactionResponse model can be serialized to JSON."""
        # Arrange
        response = TransactionResponse(
            id=str(ObjectId()),
            user_id=str(ObjectId()),
            scan_id=str(ObjectId()),
            amount=400,
            created_at="2024-01-15T12:00:00Z"
        )
        
        # Act
        response_dict = response.model_dump()
        
        # Assert
        assert "id" in response_dict
        assert "user_id" in response_dict
        assert "scan_id" in response_dict
        assert "amount" in response_dict
        assert "created_at" in response_dict
        assert response_dict["amount"] == 400
        assert response_dict["created_at"] == "2024-01-15T12:00:00Z"
    
    def test_transaction_model_default_created_at(self):
        """Test that Transaction model sets default created_at if not provided."""
        # Arrange & Act
        transaction = Transaction(
            user_id=ObjectId(),
            scan_id=ObjectId(),
            amount=500
        )
        
        # Assert
        assert transaction.created_at is not None
        assert isinstance(transaction.created_at, datetime)
        # Should be recent (within last few seconds)
        time_diff = abs((datetime.now(timezone.utc) - transaction.created_at).total_seconds())
        assert time_diff < 5  # Within 5 seconds
    
    def test_transaction_create_model_default_created_at(self):
        """Test that TransactionCreate model sets default created_at if not provided."""
        # Arrange & Act
        transaction_create = TransactionCreate(
            user_id=str(ObjectId()),
            scan_id=str(ObjectId()),
            amount=600
        )
        
        # Assert
        assert transaction_create.created_at is not None
        assert isinstance(transaction_create.created_at, datetime)
        # Should be recent (within last few seconds)
        time_diff = abs((datetime.now(timezone.utc) - transaction_create.created_at).total_seconds())
        assert time_diff < 5  # Within 5 seconds
