from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Request, Depends

from ..services.opencv_service import BottleMeasurer, MeasurementError
from ..services.roboflow_service import RoboflowClient
from ..services.validation_service import validate_scan
from ..db.mongo import mongo_db
from ..schemas.scan import ScanResponse
from ..services.iot_client import SmartBinClient
from ..services.ws_manager import manager
from ..services.reward_service import add_points
from ..middleware.auth_middleware import get_current_user
from ..models.user import User
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
    request: Request,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> Any:  # noqa: WPS110
    """Handle bottle scanning.

    Requires authentication. User context is injected by auth middleware.

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

    # Add points to authenticated user if scan is valid
    user_total_points: Optional[int] = None
    if validation_result.is_valid:
        try:
            user_total_points = await add_points(current_user, validation_result.points_awarded)
            logger.info("Added %d points to user %s. New total: %d", 
                       validation_result.points_awarded, current_user.email, user_total_points)
        except Exception as e:
            logger.error("Failed to add points for user %s: %s", current_user.email, e)
            # Continue with scan even if points addition fails
            user_total_points = current_user.points

    # 6. Store to MongoDB with user information
    try:
        if mongo_db:
            scan_document = {
                "user_id": current_user.id,
                "user_email": current_user.email,
                "brand": validation_result.brand,
                "confidence": validation_result.confidence,
                "measurement": validation_result.measurement.__dict__,
                "points": validation_result.points_awarded,
                "valid": validation_result.is_valid,
                "reason": validation_result.reason,
                "iot_events": iot_events,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await mongo_db["scans"].insert_one(scan_document)
            
            # Add scan ID to user's scan history
            if result.inserted_id:
                try:
                    from ..services.service_factory import get_user_service
                    user_service = get_user_service()
                    await user_service.add_scan_to_user(str(current_user.id), str(result.inserted_id))
                except Exception as e:
                    logger.warning("Failed to add scan to user history: %s", e)
                    
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save scan to DB: %s", exc)

    # 7. Broadcast to connected WS clients
    try:
        # Broadcast to all clients (general notification)
        await manager.broadcast({
            "type": "scan_result",
            "data": {
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "brand": validation_result.brand,
                "confidence": validation_result.confidence,
                "diameter_mm": validation_result.measurement.diameter_mm,
                "height_mm": validation_result.measurement.height_mm,
                "volume_ml": validation_result.measurement.volume_ml,
                "points": validation_result.points_awarded,
                "total_points": user_total_points,
                "valid": validation_result.is_valid,
                "events": iot_events,
                "scan_id": str(result.inserted_id) if 'result' in locals() and result.inserted_id else None,
                "debug_url": debug_url,
                "debug_image": preview_b64,
            }
        })
        
        # Send user-specific notification if user is connected
        if manager.is_user_connected(str(current_user.id)):
            await manager.broadcast_to_user(str(current_user.id), {
                "type": "personal_scan_result",
                "data": {
                    "scan_id": str(result.inserted_id) if 'result' in locals() and result.inserted_id else None,
                    "brand": validation_result.brand,
                    "confidence": validation_result.confidence,
                    "points_awarded": validation_result.points_awarded,
                    "total_points": user_total_points,
                    "valid": validation_result.is_valid,
                    "timestamp": datetime.now(timezone.utc).isoformat()
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
        debug_image=preview_b64,
        debug_url=debug_url,
    )
