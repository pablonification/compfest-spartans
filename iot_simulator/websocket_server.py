from __future__ import annotations

"""IoT Simulator – WebSocket server that emulates ESP32 SmartBin controller.

Message protocol (JSON):
Client → Server:
    {"cmd": "open"}       # request to open bin lid
    {"cmd": "close"}      # request to close lid (optional)

Server → Client sequence when receiving "open":
    {"event": "ACK", "cmd": "open"}
    {"event": "lid_opened"}
    {"event": "sensor_triggered"}
    {"event": "lid_closed"}

When receiving "close":
    {"event": "ACK", "cmd": "close"}
    {"event": "lid_closed"}

This simulator is intentionally simple and uses fixed timing to mimic motor and sensor behaviour.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict

import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("iot_simulator")

# Timing constants (seconds)
LID_OPEN_TIME = 1.5
SENSOR_TRIGGER_DELAY = 3.0
LID_CLOSE_TIME = 1.0


def json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, separators=(",", ":"))


async def handle_connection(ws: WebSocketServerProtocol):
    peer = ws.remote_address
    logger.info("Client connected: %s", peer)
    try:
        async for message in ws:
            logger.debug("Received: %s", message)
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                await ws.send(json_dumps({"error": "invalid_json"}))
                continue

            cmd = data.get("cmd")
            if cmd == "open":
                await handle_open(ws)
            elif cmd == "close":
                await handle_close(ws)
            else:
                await ws.send(json_dumps({"error": "unknown_cmd"}))
    except websockets.exceptions.ConnectionClosedOK:
        logger.info("Client %s closed connection", peer)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error in connection handler: %s", exc)


async def handle_open(ws: WebSocketServerProtocol):
    # ACK
    await ws.send(json_dumps({"event": "ACK", "cmd": "open"}))

    # Simulate lid opening
    await asyncio.sleep(LID_OPEN_TIME)
    await ws.send(json_dumps({"event": "lid_opened"}))

    # Simulate sensor trigger (bottle dropped)
    await asyncio.sleep(SENSOR_TRIGGER_DELAY)
    await ws.send(json_dumps({"event": "sensor_triggered"}))

    # Close lid
    await asyncio.sleep(LID_CLOSE_TIME)
    await ws.send(json_dumps({"event": "lid_closed"}))


async def handle_close(ws: WebSocketServerProtocol):
    await ws.send(json_dumps({"event": "ACK", "cmd": "close"}))
    await asyncio.sleep(LID_CLOSE_TIME)
    await ws.send(json_dumps({"event": "lid_closed"}))


async def main():  # pragma: no cover
    port = int(Path(__file__).parent.parent.joinpath(".env").read_text().strip() or 8080) if Path(".env").exists() else 8080
    async with websockets.serve(handle_connection, "0.0.0.0", port):
        logger.info("IoT simulator running on ws://0.0.0.0:%d", port)
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
