from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class EducationalContent(MongoBaseModel):
    """MongoDB model for educational tips/infographics."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    content_type: Literal["tip", "infographic"] = "tip"
    media_url: Optional[str] = Field(None, description="Optional image or video URL")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
