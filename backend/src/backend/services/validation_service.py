from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from .opencv_service import MeasurementResult
from .roboflow_service import Prediction

logger = logging.getLogger(__name__)

# --- Constants (could later be moved to DB or .env) -------------------------

MIN_HEIGHT_MM = 100.0  # minimal bottle height accepted (example)
MAX_HEIGHT_MM = 350.0  # maximal bottle height accepted
CONFIDENCE_THRESHOLD = 0.8  # 80%
BASE_POINTS = 10  # full reward
PENALTY_POINTS = 7  # reward when brand unknown or low confidence

# --- Result model -----------------------------------------------------------

@dataclass
class ValidationResult:
    is_valid: bool
    reason: Optional[str]
    brand: Optional[str]
    confidence: Optional[float]
    measurement: MeasurementResult
    points_awarded: int

    def to_dict(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "reason": self.reason,
            "brand": self.brand,
            "confidence": self.confidence,
            "measurement": self.measurement.__dict__,
            "points_awarded": self.points_awarded,
        }


# --- Validation Engine ------------------------------------------------------


def validate_scan(
    measurement: MeasurementResult,
    predictions: List[Prediction],
) -> ValidationResult:
    """Validate bottle scan and assign reward points.

    1. Check size constraints (height only for now; can extend to diameter).
    2. Determine top brand prediction.
    3. Decide points: full vs penalty.
    4. If size invalid → reject but still show brand prediction.
    """

    # 1. Size validation
    size_valid = MIN_HEIGHT_MM <= measurement.height_mm <= MAX_HEIGHT_MM
    
    # 2. Pick highest confidence prediction (always try to get brand info)
    top_pred: Optional[Prediction] = None
    if predictions:
        top_pred = max(predictions, key=lambda p: p.confidence)
        logger.debug("Top prediction: %s", top_pred)

    brand: Optional[str] = None
    confidence: Optional[float] = None
    points = PENALTY_POINTS  # default – penalty

    if top_pred:
        brand = top_pred.brand
        confidence = top_pred.confidence
        if confidence >= CONFIDENCE_THRESHOLD and size_valid:
            points = BASE_POINTS
        else:
            points = PENALTY_POINTS
    else:
        brand = None
        confidence = None
        points = PENALTY_POINTS

    # 3. Determine validity and reason
    if not size_valid:
        logger.info(
            "Bottle rejected due to height: %.2f mm (accepted %.0f–%.0f)",
            measurement.height_mm,
            MIN_HEIGHT_MM,
            MAX_HEIGHT_MM,
        )
        return ValidationResult(
            is_valid=False,
            reason="SIZE_OUT_OF_RANGE",
            brand=brand,  # Still show the detected brand
            confidence=confidence,  # Still show the confidence
            measurement=measurement,
            points_awarded=0,  # No points for invalid size
        )

    return ValidationResult(
        is_valid=True,
        reason=None,
        brand=brand,
        confidence=confidence,
        measurement=measurement,
        points_awarded=points,
    )
