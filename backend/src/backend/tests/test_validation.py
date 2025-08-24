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
)
from src.backend.services.opencv_service import MeasurementResult
from src.backend.services.roboflow_service import Prediction


def make_measurement(height: float, *, conf_percent: float | None = None) -> MeasurementResult:
    return MeasurementResult(
        diameter_mm=60,
        height_mm=height,
        volume_ml=600,
        classification=None,
        confidence_percent=conf_percent,
    )


def make_prediction(brand: str, confidence: float) -> Prediction:
    return Prediction({"class": brand, "confidence": confidence})


def test_validate_accept_high_confidence() -> None:
    # High size confidence (measurement close to 600ml => k_conf = 1.0) and valid height
    measurement = make_measurement(150, conf_percent=95)
    pred = make_prediction("aqua", 0.95)
    result = validate_scan(measurement, [pred])
    assert result.is_valid is True
    # For 600ml, 16g -> 0.016kg * 3700 = 59.2, with all K=1 → round to 59
    assert result.points_awarded == 59


def test_validate_low_measurement_confidence_scales_down() -> None:
    # Low size confidence (60%) -> k_conf = 0.93 bin
    measurement = make_measurement(150, conf_percent=60)
    pred = make_prediction("aqua", 0.6)
    result = validate_scan(measurement, [pred])
    # 59.2 * 0.93 ≈ 55.056 → 55
    assert result.is_valid is True
    assert result.points_awarded == 55


def test_validate_size_reject() -> None:
    measurement = make_measurement(50, conf_percent=95)  # too small
    pred = make_prediction("aqua", 0.9)
    result = validate_scan(measurement, [pred])
    assert result.is_valid is False
    assert result.points_awarded == 0
