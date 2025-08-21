from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class User(MongoBaseModel):
    email: str
    name: Optional[str] = None
    photo_url: Optional[str] = None
    points: int = 0
    role: Literal["user", "admin"] = "user"  # Default role is user
    tier: Optional[str] = None
    tier_updated_at: Optional[str] = None

    # List of scan ids (ObjectId) for reference – could be populated if needed
    scan_ids: List[PyObjectId] = Field(default_factory=list)
