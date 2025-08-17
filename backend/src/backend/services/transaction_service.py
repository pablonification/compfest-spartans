"""Transaction service for SmartBin backend."""

from __future__ import annotations

import logging
from typing import Optional, List
from datetime import datetime, timezone

from ..domain.interfaces.transaction_service import TransactionService
from ..domain.interfaces.transaction_repository import TransactionRepository
from ..models.transaction import Transaction, TransactionCreate, TransactionResponse
from ..repositories.transaction_repository import MongoDBTransactionRepository

logger = logging.getLogger(__name__)


class TransactionServiceImpl(TransactionService):
    """Implementation of transaction service."""
    
    def __init__(self, transaction_repository: TransactionRepository):
        """Initialize transaction service with repository dependency."""
        self.transaction_repository = transaction_repository
    
    async def create_transaction_after_scan(
        self, 
        user_id: str, 
        scan_id: str, 
        points_awarded: int
    ) -> Optional[Transaction]:
        """Create a transaction record after a successful bottle scan."""
        try:
            # Validate inputs
            if not user_id or not scan_id:
                logger.error("Invalid user_id or scan_id for transaction creation")
                return None
            
            if points_awarded < 0:
                logger.warning("Attempted to create transaction with negative points: %d", points_awarded)
                return None
            
            # Create transaction data
            transaction_data = TransactionCreate(
                user_id=user_id,
                scan_id=scan_id,
                amount=points_awarded
            )
            
            # Create transaction in database
            created_transaction = await self.transaction_repository.create_transaction(transaction_data)
            
            if created_transaction:
                logger.info("Successfully created transaction for scan %s: user %s, points %d", 
                           scan_id, user_id, points_awarded)
                return created_transaction
            else:
                logger.error("Failed to create transaction for scan %s", scan_id)
                return None
                
        except Exception as e:
            logger.error("Error creating transaction after scan: %s", e)
            return None
    
    async def get_user_transactions(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[TransactionResponse]:
        """Get paginated transaction history for a user."""
        try:
            # Validate inputs
            if not user_id:
                logger.error("Invalid user_id for transaction retrieval")
                return []
            
            if limit < 1 or limit > 100:
                logger.warning("Invalid limit %d, using default 20", limit)
                limit = 20
            
            if offset < 0:
                logger.warning("Invalid offset %d, using default 0", offset)
                offset = 0
            
            # Get transactions from repository
            transactions = await self.transaction_repository.get_transactions_by_user_id(
                user_id, limit, offset
            )
            
            # Convert to response models
            transaction_responses = []
            for transaction in transactions:
                response = TransactionResponse(
                    id=str(transaction.id),
                    user_id=str(transaction.user_id),
                    scan_id=str(transaction.scan_id),
                    amount=transaction.amount,
                    created_at=transaction.created_at.isoformat()
                )
                transaction_responses.append(response)
            
            logger.info("Retrieved %d transactions for user %s (limit: %d, offset: %d)", 
                       len(transaction_responses), user_id, limit, offset)
            return transaction_responses
            
        except Exception as e:
            logger.error("Error retrieving user transactions: %s", e)
            return []
    
    async def get_transaction_by_scan_id(self, scan_id: str) -> Optional[TransactionResponse]:
        """Get transaction details for a specific scan."""
        try:
            if not scan_id:
                logger.error("Invalid scan_id for transaction retrieval")
                return None
            
            # Get transaction from repository
            transaction = await self.transaction_repository.get_transaction_by_scan_id(scan_id)
            
            if transaction:
                # Convert to response model
                response = TransactionResponse(
                    id=str(transaction.id),
                    user_id=str(transaction.user_id),
                    scan_id=str(transaction.scan_id),
                    amount=transaction.amount,
                    created_at=transaction.created_at.isoformat()
                )
                return response
            
            return None
            
        except Exception as e:
            logger.error("Error retrieving transaction by scan_id %s: %s", scan_id, e)
            return None
    
    async def get_user_transaction_summary(self, user_id: str) -> dict:
        """Get aggregated transaction statistics for a user."""
        try:
            if not user_id:
                logger.error("Invalid user_id for transaction summary")
                return {}
            
            # Get summary from repository
            summary = await self.transaction_repository.get_user_transaction_summary(user_id)
            
            logger.info("Retrieved transaction summary for user %s: %s", user_id, summary)
            return summary
            
        except Exception as e:
            logger.error("Error retrieving transaction summary for user %s: %s", user_id, e)
            return {}
    
    async def get_user_transaction_count(self, user_id: str) -> int:
        """Get total number of transactions for a user."""
        try:
            if not user_id:
                logger.error("Invalid user_id for transaction count")
                return 0
            
            # Get count from repository
            count = await self.transaction_repository.get_user_transaction_count(user_id)
            
            logger.debug("User %s has %d transactions", user_id, count)
            return count
            
        except Exception as e:
            logger.error("Error retrieving transaction count for user %s: %s", user_id, e)
            return 0


# Factory function for getting transaction service
def get_transaction_service() -> TransactionService:
    """Get transaction service instance."""
    transaction_repository = MongoDBTransactionRepository()
    return TransactionServiceImpl(transaction_repository)
