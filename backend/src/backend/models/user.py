from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class User(MongoBaseModel):
    email: str
    name: Optional[str] = None
    points: int = 0

    # List of scan ids (ObjectId) for reference – could be populated if needed
    scan_ids: List[PyObjectId] = Field(default_factory=list)
