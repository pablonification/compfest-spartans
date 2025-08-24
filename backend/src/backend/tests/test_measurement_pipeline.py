# pylint: disable=invalid-name
"""Quick CLI & test for measuring sample bottles.

You can either run this file directly:

```bash
python backend/src/backend/tests/test_measurement_pipeline.py
```

or execute it via pytest to get proper assertions:

```bash
pytest backend/src/backend/tests/test_measurement_pipeline.py -v
```
"""

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make sure `backend` package is importable even when running this file as a
# standalone script from arbitrary working directories. We prepend the
# "backend/src" directory (containing the package) to sys.path.
# ---------------------------------------------------------------------------

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[4]  # compsfest/
BACKEND_SRC = PROJECT_ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

# Now regular imports will work
from src.backend.services.opencv_service import BottleMeasurer, MeasurementError

SAMPLES: list[tuple[str, float]] = [
    ("testing/test2.1.jpg", 1500.0),
    ("testing/test2.4.jpg", 330.0),
    ("testing/test2.8.jpg", 600.0),
]

def main():
    project_root = Path(__file__).resolve().parents[4]
    all_passed = True

    for rel_path, expected_ml in SAMPLES:
        img_path = project_root / rel_path
        if not img_path.exists():
            print(f"Sample image not found: {img_path}")
            all_passed = False
            continue

        img_bytes = img_path.read_bytes()
        measurer = BottleMeasurer(classify=False)

        try:
            result, preview = measurer.measure(img_bytes, return_debug=True)  # type: ignore[assignment]
        except MeasurementError as exc:
            print(f"Measurement failed for {rel_path}: {exc}")
            all_passed = False
            continue

        debug_dir = project_root / "debug_test_outputs"
        debug_dir.mkdir(exist_ok=True)
        debug_path = debug_dir / Path(rel_path).name.replace(".jpg", "_debug.jpg")
        debug_path.write_bytes(preview)

        print(
            f"{rel_path}: H={result.height_mm:.1f} mm, D={result.diameter_mm:.1f} mm, V={result.volume_ml:.0f} mL"
        )

        allowed_error = 0.30 * expected_ml
        diff = abs(result.volume_ml - expected_ml)

        if diff > allowed_error:
            print(
                f"[FAIL] Estimated volume for {rel_path} deviates by {diff:.1f} mL "
                f"(allowed ±{allowed_error:.0f}). Got {result.volume_ml:.1f} mL, "
                f"expected ≈{expected_ml:.1f} mL."
            )
            all_passed = False
        else:
            print(f"[PASS] {rel_path}")

    if all_passed:
        print("All samples passed.")
    else:
        print("Some samples failed.")

if __name__ == "__main__":
    main()
