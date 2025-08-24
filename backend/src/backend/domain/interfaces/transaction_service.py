"""Transaction service interface for SmartBin backend."""

from __future__ import annotations

from typing import Protocol, Optional, List

from src.backend.models.transaction import Transaction, TransactionCreate, TransactionResponse


class TransactionService(Protocol):
    """Protocol interface for transaction business operations."""
    
    async def create_transaction_after_scan(
        self, 
        user_id: str, 
        scan_id: str, 
        points_awarded: int
    ) -> Optional[Transaction]:
        """Create a transaction record after a successful bottle scan."""
        ...
    
    async def get_user_transactions(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[TransactionResponse]:
        """Get paginated transaction history for a user."""
        ...
    
    async def get_transaction_by_scan_id(self, scan_id: str) -> Optional[TransactionResponse]:
        """Get transaction details for a specific scan."""
        ...
    
    async def get_user_transaction_summary(self, user_id: str) -> dict:
        """Get aggregated transaction statistics for a user."""
        ...
    
    async def get_user_transaction_count(self, user_id: str) -> int:
        """Get total number of transactions for a user."""
        ...
