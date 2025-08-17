from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.ws_manager import manager  # singleton

router = APIRouter()


@router.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket):  # noqa: D401
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection open; ignore content
    except WebSocketDisconnect:
        manager.disconnect(websocket)
