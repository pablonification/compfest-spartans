"""Test transaction router functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from bson import ObjectId

from ..routers.transactions import router
from ..models.transaction import TransactionResponse
from ..services.transaction_service import TransactionService

# Create test client
client = TestClient(router)


class TestTransactionRouter:
    """Test transaction router endpoints."""
    
    @pytest.fixture
    def mock_transaction_service(self):
        """Create a mock transaction service."""
        mock_service = AsyncMock(spec=TransactionService)
        return mock_service
    
    @pytest.fixture
    def sample_transaction_response(self):
        """Sample transaction response for testing."""
        return TransactionResponse(
            id=str(ObjectId()),
            user_id="user@example.com",
            scan_id=str(ObjectId()),
            amount=100,
            created_at="2024-01-15T10:00:00Z"
        )
    
    @pytest.fixture
    def mock_auth_payload(self):
        """Mock authentication payload."""
        return {"email": "user@example.com"}
    
    async def test_get_user_transactions_success(self, mock_transaction_service, sample_transaction_response, mock_auth_payload):
        """Test successful retrieval of user transactions."""
        # Arrange
        mock_transaction_service.get_user_transactions.return_value = [sample_transaction_response]
        
        # Mock the auth dependency
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act
        response = client.get("/transactions?limit=10&offset=0")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_transaction_response.id
        assert data[0]["user_id"] == sample_transaction_response.user_id
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_get_user_transactions_pagination(self, mock_transaction_service, mock_auth_payload):
        """Test transaction pagination parameters."""
        # Arrange
        mock_transaction_service.get_user_transactions.return_value = []
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act - Test valid pagination
        response = client.get("/transactions?limit=50&offset=10")
        
        # Assert
        assert response.status_code == 200
        
        # Act - Test invalid limit (too high)
        response = client.get("/transactions?limit=150&offset=0")
        
        # Assert
        assert response.status_code == 422  # Validation error
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_get_transaction_details_success(self, mock_transaction_service, sample_transaction_response, mock_auth_payload):
        """Test successful retrieval of transaction details."""
        # Arrange
        mock_transaction_service.get_transaction_by_scan_id.return_value = sample_transaction_response
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act
        response = client.get(f"/transactions/{sample_transaction_response.scan_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_transaction_response.id
        assert data["amount"] == sample_transaction_response.amount
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_get_transaction_details_not_found(self, mock_transaction_service, mock_auth_payload):
        """Test transaction details when transaction doesn't exist."""
        # Arrange
        mock_transaction_service.get_transaction_by_scan_id.return_value = None
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act
        response = client.get("/transactions/nonexistent_id")
        
        # Assert
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_get_user_transaction_summary_success(self, mock_transaction_service, mock_auth_payload):
        """Test successful retrieval of user transaction summary."""
        # Arrange
        mock_summary = {
            "total_transactions": 5,
            "total_points": 500,
            "average_points": 100.0
        }
        mock_transaction_service.get_user_transaction_summary.return_value = mock_summary
        mock_transaction_service.get_user_transaction_count.return_value = 5
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act
        response = client.get("/transactions/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 5
        assert data["total_points"] == 500
        assert data["average_points"] == 100.0
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_get_user_transaction_count_success(self, mock_transaction_service, mock_auth_payload):
        """Test successful retrieval of user transaction count."""
        # Arrange
        mock_transaction_service.get_user_transaction_count.return_value = 15
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act
        response = client.get("/transactions/count")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 15
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_authentication_required(self):
        """Test that authentication is required for all endpoints."""
        # Test without authentication
        endpoints = [
            "/transactions",
            "/transactions/summary",
            "/transactions/count",
            "/transactions/some_id"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 422  # Missing dependency
    
    async def test_invalid_auth_token(self):
        """Test behavior with invalid authentication token."""
        # Arrange
        invalid_payload = {"email": None}
        router.dependency_overrides[verify_token] = lambda: invalid_payload
        
        # Act
        response = client.get("/transactions")
        
        # Assert
        assert response.status_code == 401
        assert "Invalid user token" in response.json()["detail"]
        
        # Cleanup
        router.dependency_overrides.clear()
    
    async def test_service_error_handling(self, mock_transaction_service, mock_auth_payload):
        """Test error handling when service layer fails."""
        # Arrange
        mock_transaction_service.get_user_transactions.side_effect = Exception("Service error")
        router.dependency_overrides[verify_token] = lambda: mock_auth_payload
        
        # Act
        response = client.get("/transactions")
        
        # Assert
        assert response.status_code == 500
        assert "Failed to fetch transaction history" in response.json()["detail"]
        
        # Cleanup
        router.dependency_overrides.clear()
