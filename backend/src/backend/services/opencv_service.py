from __future__ import annotations

import math
import logging
from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MeasurementResult:
    """Bottle measurement in millimeters and volume in milliliters."""

    diameter_mm: float
    height_mm: float
    volume_ml: float


class MeasurementError(RuntimeError):
    pass


class BottleMeasurer:
    """Measure bottle dimensions using a coloured reference object for scale calibration.

    The algorithm expects a solid-colour reference rectangle (or any blob) at the
    bottom of the frame. Region of interest (ROI) above that reference will be
    analysed to detect the bottle silhouette.
    """

    def __init__(
        self,
        ref_real_width_mm: float = 30.0,
        ref_hsv_lower: Tuple[int, int, int] = (20, 100, 100),  # default: yellow-ish
        ref_hsv_upper: Tuple[int, int, int] = (30, 255, 255),
    ) -> None:
        self.ref_real_width_mm = ref_real_width_mm
        self.ref_hsv_lower = np.array(ref_hsv_lower, dtype=np.uint8)
        self.ref_hsv_upper = np.array(ref_hsv_upper, dtype=np.uint8)

    def _find_reference(self, hsv: np.ndarray) -> Tuple[int, int, int, int]:
        """Return bounding box (x, y, w, h) of reference object in HSV image."""
        mask = cv2.inRange(hsv, self.ref_hsv_lower, self.ref_hsv_upper)
        # Morphological cleanup
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise MeasurementError("Reference object not found in image.")
        # Choose the largest contour as reference
        contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(contour)
        if w < 10 or h < 10:  # sanity check
            raise MeasurementError("Reference object size too small.")
        logger.debug("Reference bbox: x=%d y=%d w=%d h=%d", x, y, w, h)
        return x, y, w, h

    def _extract_bottle_contour(self, roi_gray: np.ndarray) -> np.ndarray:
        """Return contour corresponding to the bottle silhouette."""
        # Edge detection & thresholding
        blur = cv2.GaussianBlur(roi_gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Invert (bottle is darker/lighter?) – choose largest contour regardless
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            raise MeasurementError("No contours found in ROI for bottle.")
        contour = max(contours, key=cv2.contourArea)
        return contour

    def measure(self, image_bytes: bytes) -> MeasurementResult:
        # Decode image bytes to BGR
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise MeasurementError("Invalid image data provided.")

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        x_ref, y_ref, w_ref, h_ref = self._find_reference(hsv)

        # Pixels per mm scale
        scale = self.ref_real_width_mm / w_ref  # mm per pixel
        logger.debug("Scale: %.4f mm/pixel", scale)

        # Define ROI above the reference object
        roi = img[: y_ref, :]
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Find bottle contour
        contour = self._extract_bottle_contour(roi_gray)
        x, y, w, h = cv2.boundingRect(contour)

        height_mm = h * scale
        diameter_mm = w * scale

        # Volume estimation (cylinder approximation)
        radius_cm = (diameter_mm / 10) / 2  # convert to cm
        height_cm = height_mm / 10
        volume_cm3 = math.pi * radius_cm**2 * height_cm
        volume_ml = volume_cm3  # 1 cm3 = 1 ml

        logger.debug(
            "Measured bottle – diameter_mm=%.2f height_mm=%.2f volume_ml=%.2f",
            diameter_mm,
            height_mm,
            volume_ml,
        )

        return MeasurementResult(
            diameter_mm=round(diameter_mm, 2),
            height_mm=round(height_mm, 2),
            volume_ml=round(volume_ml, 2),
        )
