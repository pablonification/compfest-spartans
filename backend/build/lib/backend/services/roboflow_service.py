from __future__ import annotations

import base64
import json
import logging
from typing import Any, List

import httpx

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class Prediction(BaseException):
    brand: str
    confidence: float
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None

    def __init__(self, data: dict[str, Any]):
        self.brand = data.get("class", "unknown")
        self.confidence = float(data.get("confidence", 0))
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
        self.model_id = model_id or getattr(settings, "ROBOFLOW_MODEL_ID", "uascv/klasifikasi-per-merk/3")
        self.api_url = f"https://serverless.roboflow.com/{self.model_id}?api_key={self.api_key}"

    async def predict(self, image_bytes: bytes) -> List[Prediction]:
        """Send image to Roboflow and return list of predictions."""
        encoded = base64.b64encode(image_bytes).decode()
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.api_url, content=encoded, headers=headers)
            response.raise_for_status()
            data = response.json()

        predictions_data = data.get("predictions", [])
        predictions = [Prediction(p) for p in predictions_data]
        logger.debug("Roboflow predictions: %s", predictions)
        return predictions


# Utility function for synchronous usage if needed

def predict_sync(image_bytes: bytes, api_key: str | None = None, model_id: str | None = None) -> List[Prediction]:
    client = RoboflowClient(api_key, model_id)
    encoded = base64.b64encode(image_bytes).decode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = httpx.post(client.api_url, content=encoded, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return [Prediction(p) for p in data.get("predictions", [])]
