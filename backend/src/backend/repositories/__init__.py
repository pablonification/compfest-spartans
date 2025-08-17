"""Repositories package for SmartBin backend."""

from .transaction_repository import MongoDBTransactionRepository

__all__ = [
    "MongoDBTransactionRepository",
]
