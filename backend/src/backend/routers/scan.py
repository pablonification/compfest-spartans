from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime, timezone
import base64, binascii
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Header

from ..services.opencv_service import BottleMeasurer, MeasurementError
from ..services.roboflow_service import RoboflowClient
from ..services.validation_service import validate_scan
from ..db.mongo import mongo_db
from ..schemas.scan import ScanResponse
from ..services.iot_client import SmartBinClient
from ..services.ws_manager import manager
from ..services.reward_service import add_points

router = APIRouter()
logger = logging.getLogger(__name__)

bottle_measurer = BottleMeasurer()  # default settings; could be injected
roboflow_client = RoboflowClient()
smartbin_client = SmartBinClient()


@router.post("/scan", response_model=ScanResponse, status_code=status.HTTP_200_OK)
async def scan_bottle(
    image: UploadFile = File(...),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
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

    # 2. OpenCV measurement
    try:
        measurement = bottle_measurer.measure(content)
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

    # Add points to user if scan is valid and user email provided
    user_total_points: Optional[int] = None
    if validation_result.is_valid and x_user_email:
        try:
            user_total_points = await add_points(x_user_email, validation_result.points_awarded)
            logger.info("Added %d points to user %s. New total: %d",
                       validation_result.points_awarded, x_user_email, user_total_points)
        except Exception as e:
            logger.error("Failed to add points for user %s: %s", x_user_email, e)
            # Continue with scan even if points addition fails

    # Debug image handling (from dev branch)
    debug_url = None
    preview_b64 = None
    try:
        # Save debug image with unique name
        debug_filename = f"debug_{uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        debug_path = Path("debug_images") / debug_filename
        debug_path.parent.mkdir(exist_ok=True)
        
        with open(debug_path, "wb") as f:
            f.write(content)
        
        debug_url = f"/debug/{debug_filename}"
        
        # Create base64 preview for WebSocket
        preview_b64 = base64.b64encode(content).decode('ascii')
        logger.debug("Saved debug image: %s", debug_path)
        
    except Exception as e:
        logger.warning("Failed to save debug image: %s", e)

    # 6. Store to MongoDB
    try:
        if mongo_db:
            scan_document = {
                "user_email": x_user_email,
                "brand": validation_result.brand,
                "confidence": validation_result.confidence,
                "measurement": validation_result.measurement.__dict__,
                "points": validation_result.points_awarded,
                "valid": validation_result.is_valid,
                "reason": validation_result.reason,
                "iot_events": iot_events,
                "debug_url": debug_url,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            await mongo_db["scans"].insert_one(scan_document)

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save scan to DB: %s", exc)

    # 7. Broadcast to connected WS clients
    try:
        await manager.broadcast({
            "type": "scan_result",
            "data": {
                "user_email": x_user_email,
                "brand": validation_result.brand,
                "confidence": validation_result.confidence,
                "diameter_mm": validation_result.measurement.diameter_mm,
                "height_mm": validation_result.measurement.height_mm,
                "volume_ml": validation_result.measurement.volume_ml,
                "points": validation_result.points_awarded,
                "total_points": user_total_points,
                "valid": validation_result.is_valid,
                "events": iot_events,
                "debug_url": debug_url,
                "debug_image": preview_b64,
            }
        })

    except Exception as e:
        logger.error("Failed to broadcast scan result: %s", e)
        # Continue with response even if WebSocket broadcast fails

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
    )
