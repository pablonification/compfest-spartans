from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend package importable when running as script
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[4]
BACKEND_SRC = PROJECT_ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from src.backend.services.validation_service import (
    validate_scan,
    PENALTY_POINTS,
    BASE_POINTS,
    CONFIDENCE_THRESHOLD,
)
from src.backend.services.opencv_service import MeasurementResult
from src.backend.services.roboflow_service import Prediction


def make_measurement(height: float) -> MeasurementResult:
    return MeasurementResult(diameter_mm=60, height_mm=height, volume_ml=600)


def make_prediction(brand: str, confidence: float) -> Prediction:
    return Prediction({"class": brand, "confidence": confidence})


def test_validate_accept_high_confidence() -> None:
    measurement = make_measurement(150)  # within size range
    pred = make_prediction("aqua", CONFIDENCE_THRESHOLD + 0.05)
    result = validate_scan(measurement, [pred])
    assert result.is_valid is True
    assert result.points_awarded == BASE_POINTS


def test_validate_penalty_low_confidence() -> None:
    measurement = make_measurement(150)
    pred = make_prediction("aqua", CONFIDENCE_THRESHOLD - 0.2)
    result = validate_scan(measurement, [pred])
    assert result.points_awarded == PENALTY_POINTS


def test_validate_size_reject() -> None:
    measurement = make_measurement(50)  # too small
    pred = make_prediction("aqua", CONFIDENCE_THRESHOLD + 0.1)
    result = validate_scan(measurement, [pred])
    assert result.is_valid is False
    assert result.points_awarded == 0
