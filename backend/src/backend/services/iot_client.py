from __future__ import annotations

import asyncio
import json
import logging
from typing import List

import websockets

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class SmartBinClient:
    """Client to control SmartBin via WebSocket."""

    def __init__(self, ws_url: str | None = None):
        self.ws_url = ws_url or get_settings().IOT_WS_URL

    async def open_bin(self) -> List[str]:
        """Send open command and await event sequence; returns list of events."""
        events: List[str] = []
        try:
            async with websockets.connect(self.ws_url, ping_interval=None) as ws:
                await ws.send(json.dumps({"cmd": "open"}))
                # Wait until lid_closed event received or timeout
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=10)
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for events from bin")
                        break
                    data = json.loads(message)
                    event = data.get("event")
                    if event:
                        events.append(event)
                        if event == "lid_closed":
                            break
        except Exception as exc:  # noqa: BLE001
            logger.error("IoT communication error: %s", exc)
        return events
