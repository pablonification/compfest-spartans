"""Transaction repository interface for SmartBin backend."""

from __future__ import annotations

from typing import Protocol, Optional, List
from bson import ObjectId

from ...models.transaction import Transaction, TransactionCreate


class TransactionRepository(Protocol):
    """Protocol interface for transaction data operations."""
    
    async def create_transaction(self, transaction: TransactionCreate) -> Optional[Transaction]:
        """Create a new transaction record."""
        ...
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID."""
        ...
    
    async def get_transactions_by_user_id(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for a specific user with pagination."""
        ...
    
    async def get_transaction_by_scan_id(self, scan_id: str) -> Optional[Transaction]:
        """Get transaction by scan ID (one-to-one relationship)."""
        ...
    
    async def get_user_transaction_count(self, user_id: str) -> int:
        """Get total number of transactions for a user."""
        ...
    
    async def get_user_transaction_summary(self, user_id: str) -> dict:
        """Get aggregated transaction statistics for a user."""
        ...
