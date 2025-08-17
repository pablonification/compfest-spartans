from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class EducationalBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    content_type: Literal["tip", "infographic"] = "tip"
    media_url: Optional[str] = None


class EducationalCreate(EducationalBase):
    pass


class EducationalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    content_type: Optional[Literal["tip", "infographic"]] = None
    media_url: Optional[str] = None


class EducationalResponse(EducationalBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Kenapa botol plastik harus dipipihkan?",
                "description": "Memipihkan botol mengurangi volume sampah hingga 60% dan mencegah air menggenang.",
                "content_type": "tip",
                "media_url": "https://example.com/images/flatten_bottle.jpg",
                "created_at": "2025-08-17T09:00:00Z",
                "updated_at": "2025-08-17T09:00:00Z"
            }
        }


class EducationalListResponse(BaseModel):
    items: list[EducationalResponse]
    total: int
