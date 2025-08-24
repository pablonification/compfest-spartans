from __future__ import annotations

import logging
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from ..core.config import get_settings
from ..db.mongo import ensure_connection

logger = logging.getLogger(__name__)


class ESP32Client:
    """Client to control ESP32 SmartBin devices via HTTP API."""
    
    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or getattr(settings, "ESP32_API_URL", "https://api.setorin.app")
        self.timeout = aiohttp.ClientTimeout(total=15)  # 15 second timeout
    
    async def control_esp32_lid(self, device_id: str, duration_seconds: int = 3) -> Dict[str, Any]:
        """Control ESP32 lid via HTTP API and return events for compatibility."""
        try:
            db = await ensure_connection()
            
            # Create log entry
            log_result = await db["esp32_logs"].insert_one({
                "device_id": device_id,
                "action": "open",
                "timestamp": datetime.now(timezone.utc),
                "status": "pending",
                "details": {"duration_seconds": duration_seconds},
                "source": "scan_integration"
            })
            
            action_id = str(log_result.inserted_id)
            logger.info("Created ESP32 action log with ID: %s for device: %s", action_id, device_id)
            
            # Make HTTP call to ESP32 control endpoint
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                payload = {
                    "device_id": device_id,
                    "action": "open",
                    "duration_seconds": duration_seconds
                }
                
                control_url = f"{self.base_url}/api/esp32/control"
                logger.info("Calling ESP32 control API: %s", control_url)
                
                async with session.post(
                    control_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("ESP32 control successful: %s", result)
                        
                        # Update log as initiated
                        await db["esp32_logs"].update_one(
                            {"_id": log_result.inserted_id},
                            {"$set": {"status": "initiated", "api_response": result}}
                        )
                        
                        # Return events in format expected by scan flow
                        return {
                            "events": ["lid_opening", "lid_opened", "waiting", "lid_closing", "lid_closed"],
                            "action_id": action_id,
                            "device_id": device_id,
                            "api_response": result
                        }
                    else:
                        error_text = await response.text()
                        error_msg = f"ESP32 API error: {response.status} - {error_text}"
                        logger.error(error_msg)
                        
                        # Update log as error
                        await db["esp32_logs"].update_one(
                            {"_id": log_result.inserted_id},
                            {"$set": {"status": "error", "error_message": error_msg}}
                        )
                        
                        raise Exception(error_msg)
                        
        except Exception as exc:
            logger.error("ESP32 control failed: %s", exc)
            
            # Update log as error
            try:
                await db["esp32_logs"].update_one(
                    {"_id": log_result.inserted_id},
                    {"$set": {"status": "error", "error_message": str(exc)}}
                )
            except:
                pass
                
            return {"events": [], "error": str(exc), "action_id": action_id}
    
    async def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get list of online ESP32 devices."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                devices_url = f"{self.base_url}/api/esp32/devices"
                
                async with session.get(devices_url) as response:
                    if response.status == 200:
                        devices = await response.json()
                        # Filter for online devices
                        online_devices = [d for d in devices if d.get("status") == "online"]
                        logger.info("Found %d online ESP32 devices", len(online_devices))
                        return online_devices
                    else:
                        logger.warning("Failed to get ESP32 devices: %s", response.status)
                        return []
                        
        except Exception as exc:
            logger.error("Failed to get ESP32 devices: %s", exc)
            return []
    
    async def select_best_device(self) -> Optional[str]:
        """Select the best available ESP32 device for lid control."""
        devices = await self.get_available_devices()
        
        if not devices:
            logger.warning("No online ESP32 devices available")
            return None
        
        # For now, select the first online device
        # In future, could implement load balancing, proximity, etc.
        selected_device = devices[0]
        device_id = selected_device["device_id"]
        
        logger.info("Selected ESP32 device: %s (location: %s)", 
                   device_id, selected_device.get("location", "Unknown"))
        return device_id
    
    async def open_bin(self) -> List[str]:
        """
        Main interface method - compatible with existing SmartBinClient.
        Automatically selects an available ESP32 device and opens the lid.
        """
        settings = get_settings()
        
        # Check if ESP32 is enabled
        if not settings.ESP32_ENABLED:
            logger.info("ESP32 integration disabled, returning empty events")
            return []
        
        try:
            # Select best available device
            device_id = await self.select_best_device()
            
            if not device_id:
                logger.warning("No ESP32 devices available, returning empty events")
                return []
            
            # Control the selected device
            result = await self.control_esp32_lid(device_id, duration_seconds=3)
            
            if "error" in result:
                logger.error("ESP32 lid control failed: %s", result["error"])
                return []
            
            return result.get("events", [])
            
        except Exception as exc:
            logger.error("ESP32 open_bin failed: %s", exc)
            return []


# Global instance for compatibility with existing code
esp32_client = ESP32Client()
