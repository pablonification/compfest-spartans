from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class Transaction(MongoBaseModel):
    """Transaction model for tracking user rewards and bottle scans."""
    
    user_id: PyObjectId
    scan_id: PyObjectId
    amount: int  # Points awarded
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class TransactionCreate(MongoBaseModel):
    """Model for creating new transactions."""
    
    user_id: str
    scan_id: str
    amount: int
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TransactionResponse(MongoBaseModel):
    """Transaction response model for API endpoints."""
    
    id: str
    user_id: str
    scan_id: str
    amount: int
    created_at: str
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
