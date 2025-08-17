from __future__ import annotations

import logging
from typing import Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Header, Depends

from ..services.opencv_service import BottleMeasurer, MeasurementError
from ..services.roboflow_service import RoboflowClient
from ..services.validation_service import validate_scan
from ..db.mongo import mongo_db, get_database
from ..schemas.scan import ScanResponse
from ..services.iot_client import SmartBinClient
from ..services.ws_manager import manager
from ..services.reward_service import add_points
from ..routers.auth import verify_token
import base64, binascii
from pathlib import Path
from uuid import uuid4

router = APIRouter()
logger = logging.getLogger(__name__)

bottle_measurer = BottleMeasurer()  # default settings; could be injected
roboflow_client = RoboflowClient()
smartbin_client = SmartBinClient()


@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_200_OK)
async def scan_bottle(
    image: UploadFile = File(...),
    payload: dict = Depends(verify_token),
) -> Any:  # noqa: WPS110
    """Handle bottle scanning.

    1. Read image bytes.
    2. Run OpenCV measurement.
    3. Call Roboflow for brand prediction.
    4. Validate and compute reward.
    5. Store result in MongoDB.
    6. Return validation payload.
    """

    content = await image.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty image upload")

    # Get user email from JWT payload
    user_email = payload.get("email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid user token")

    # 2. OpenCV measurement (with debug preview)
    try:
        measurement, preview_bytes = bottle_measurer.measure(content, return_debug=True)
        preview_b64: str | None = base64.b64encode(preview_bytes).decode()
        # save preview image to disk
        debug_dir = Path("debug_images")
        debug_dir.mkdir(exist_ok=True)
        filename = f"{uuid4().hex}.jpg"
        (debug_dir / filename).write_bytes(preview_bytes)
        debug_url = f"/debug/{filename}"
    except MeasurementError as exc:
        logger.warning("Measurement failed: %s", exc)
        raise HTTPException(status_code=422, detail="Unable to measure bottle") from exc

    # 3. Roboflow predictions
    try:
        predictions = await roboflow_client.predict(content)
    except Exception as exc:  # noqa: BLE001
        logger.error("Roboflow error: %s", exc)
        raise HTTPException(status_code=502, detail="Error contacting AI service") from exc

    # 4. Validation
    validation_result = validate_scan(measurement, predictions)

    # 5. Open bin via IoT if valid
    iot_events = []
    if validation_result.is_valid:
        iot_events = await smartbin_client.open_bin()

    user_total_points: Optional[int] = None
    if validation_result.is_valid and user_email:
        user_total_points = await add_points(user_email, validation_result.points_awarded)

    # 6. Store to MongoDB (best-effort)
    try:
        if mongo_db:
            await mongo_db["scans"].insert_one({
                "brand": validation_result.brand,
                "confidence": validation_result.confidence,
                "measurement": validation_result.measurement.__dict__,
                "points": validation_result.points_awarded,
                "valid": validation_result.is_valid,
                "reason": validation_result.reason,
                "iot_events": iot_events,
                "user_email": user_email,
                "timestamp": datetime.now(timezone.utc),
            })
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save scan to DB: %s", exc)

    # 7. Broadcast to connected WS clients
    await manager.broadcast({
        "type": "scan_result",
        "data": {
            "brand": validation_result.brand,
            "confidence": validation_result.confidence,
            "diameter_mm": validation_result.measurement.diameter_mm,
            "height_mm": validation_result.measurement.height_mm,
            "volume_ml": validation_result.measurement.volume_ml,
            "points": validation_result.points_awarded,
            "total_points": user_total_points,
            "valid": validation_result.is_valid,
            "events": iot_events,
            "email": user_email,
            "debug_url": debug_url,
            "debug_image": preview_b64,
        }
    })

    # 8. Return response
    return ScanResponse(
        is_valid=validation_result.is_valid,
        reason=validation_result.reason,
        brand=validation_result.brand,
        confidence=validation_result.confidence,
        diameter_mm=validation_result.measurement.diameter_mm,
        height_mm=validation_result.measurement.height_mm,
        volume_ml=validation_result.measurement.volume_ml,
        points_awarded=validation_result.points_awarded,
        total_points=user_total_points,
        debug_image=preview_b64,
        debug_url=debug_url,
    )


@router.get("/transactions", response_model=List[dict])
async def get_user_transactions(payload: dict = Depends(verify_token)):
    """Get user's scan and reward history"""
    try:
        user_email = payload.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        db = get_database()
        scans_collection = db.scans
        
        # Get user's scan history
        user_scans = await scans_collection.find(
            {"user_email": user_email},
            {"_id": 0, "user_email": 0}  # Exclude sensitive fields
        ).sort("timestamp", -1).to_list(length=100)  # Limit to last 100 scans
        
        return user_scans
        
    except Exception as exc:
        logger.error("Failed to fetch user transactions: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch transaction history")
