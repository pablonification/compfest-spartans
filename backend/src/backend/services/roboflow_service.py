# Refactored to use inference-sdk HTTP client instead of manual HTTP calls

from __future__ import annotations

import asyncio
import logging
from typing import Any, List
import io
import numpy as np
from PIL import Image

# Third-party HTTP fallback (requests is already in dependencies)
import requests

from inference_sdk import InferenceHTTPClient

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class Prediction:
    brand: str
    confidence: float
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None

    def __init__(self, data: dict[str, Any]):
        # Roboflow classification payloads sometimes use different keys depending
        # on the model type (detection vs classification). Try a few common ones
        # to maximise compatibility.
        self.brand = (
            data.get("class")
            or data.get("label")  # classification REST endpoint
            or data.get("name")
            or "unknown"
        )

        # Confidence/probability might be returned under several field names.
        conf_raw = (
            data.get("confidence")
            or data.get("probability")
            or data.get("confidence_score")
            or 0.0
        )
        self.confidence = float(conf_raw)
        self.x = data.get("x")
        self.y = data.get("y")
        self.width = data.get("width")
        self.height = data.get("height")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Prediction brand={self.brand} conf={self.confidence:.2f}>"


class RoboflowClient:
    """Client to interact with Roboflow Hosted Inference API."""
    def __init__(self, api_key: str | None = None, model_id: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "ROBOFLOW_API_KEY", None) or ""
        self.model_id = model_id or getattr(settings, "ROBOFLOW_MODEL_ID", "klasifikasi-per-merk/3")

        # Single shared synchronous client (thread-safe)
        self._client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=self.api_key,
        )

    async def predict(self, image_bytes: bytes) -> List[Prediction]:
        """Send image to Roboflow and return list of predictions using the official SDK."""

        loop = asyncio.get_running_loop()

        # Decode image bytes into a NumPy array
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(pil_image)
        except Exception as exc:
            logger.error("Failed to decode image bytes: %s", exc)
            raise

        def _infer_sdk() -> Any:
            """Primary inference path using the official inference SDK."""
            return self._client.infer(image_np, model_id=self.model_id)

        def _infer_http() -> Any:
            """Fallback inference using the raw HTTP classification endpoint.

            This path is used when the SDK returns 0 predictions which can happen
            with Roboflow *classification* models that are not yet fully
            supported by the unified `serverless.roboflow.com` endpoint.
            """
            url = f"https://classify.roboflow.com/{self.model_id}"
            params = {"api_key": self.api_key}
            files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
            resp = requests.post(url, params=params, files=files, timeout=30)
            resp.raise_for_status()
            return resp.json()

        try:
            data: dict[str, Any] = await loop.run_in_executor(None, _infer_sdk)
        except Exception as exc:  # noqa: BLE001
            logger.error("Roboflow SDK error: %s", exc)
            raise

        predictions_data = data.get("predictions", [])

        # Fallback to raw HTTP endpoint if SDK returned no predictions (can
        # happen for classification models).
        if not predictions_data:
            try:
                data = await loop.run_in_executor(None, _infer_http)
                predictions_data = data.get("predictions", [])
            except Exception as exc:  # noqa: BLE001
                # Keep the original empty result but log for troubleshooting.
                logger.warning("Roboflow HTTP fallback failed: %s", exc)

        predictions = [Prediction(p) for p in predictions_data]
        logger.debug("Roboflow predictions: %s", predictions)
        return predictions


# Utility function for synchronous usage if needed

def predict_sync(image_bytes: bytes, api_key: str | None = None, model_id: str | None = None) -> List[Prediction]:
    client = RoboflowClient(api_key, model_id)
    # The original code used base64 encoding, but the new code uses the SDK directly.
    # If base64 encoding is still needed, it should be re-added here.
    # For now, we'll just pass the image_bytes directly to the SDK.
    return client.predict(image_bytes)
