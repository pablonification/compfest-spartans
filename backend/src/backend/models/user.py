from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class User(MongoBaseModel):
    email: str
    name: Optional[str] = None
    points: int = 0
    google_id: Optional[str] = None  # Google OAuth ID
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # List of scan ids (ObjectId) for reference – could be populated if needed
    scan_ids: List[PyObjectId] = Field(default_factory=list)
