from __future__ import annotations

from typing import Optional

from pydantic import Field

from .common import MongoBaseModel, PyObjectId


class MeasurementDocument(MongoBaseModel):
    diameter_mm: float
    height_mm: float
    volume_ml: float


class BottleScan(MongoBaseModel):
    user_id: Optional[PyObjectId] = None  # can be null for anonymous
    brand: Optional[str] = None
    confidence: Optional[float] = None
    measurement: MeasurementDocument
    points: int = 0
    valid: bool = True
    reason: Optional[str] = None
