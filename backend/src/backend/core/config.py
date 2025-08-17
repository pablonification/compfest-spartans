import os
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables."""

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/smartbin")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "smartbin")
    IOT_WS_URL: str = os.getenv("IOT_WS_URL", "ws://iot_simulator:8080")

    # Roboflow inference
    ROBOFLOW_API_KEY: str = os.getenv("ROBOFLOW_API_KEY", "")
    # Format: <workspace>/<model_name>/<version>
    ROBOFLOW_MODEL_ID: str = os.getenv("ROBOFLOW_MODEL_ID", "klasifikasi-per-merk/3")


@lru_cache
def get_settings() -> Settings:  # pragma: no cover
    return Settings()
