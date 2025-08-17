from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class ScanResponse(BaseModel):
    scan_id: Optional[str] = None
    transaction_id: Optional[str] = None
    is_valid: bool
    reason: Optional[str] = None
    brand: Optional[str] = None
    confidence: Optional[float] = None

    diameter_mm: float
    height_mm: float
    volume_ml: float

    points_awarded: int
    total_points: Optional[int] = None
    debug_image: str | None = None  # base64 JPEG with reference/bboxes
    debug_url: str | None = None
