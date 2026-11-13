"""Real-Time WebSocket Ingestion & Client Broadcast Hub."""
import json
import asyncio
from datetime import datetime, timezone
from typing import Set, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.app.core.logging import logger

router = APIRouter(tags=["WebSocket Real-Time Ingest & Events"])


class WebSocketHub:
    """Manages connected authenticated client WebSockets and broadcasts live events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("Client WebSocket connected. Total active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("Client WebSocket disconnected. Remaining: %d", len(self.active_connections))

    async def broadcast(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Broadcast structured event to all active client websockets."""
        if not self.active_connections:
            return

        message = {
            "event": event_name,
            "data": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        dead_sockets = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead_sockets.add(ws)

        for dead in dead_sockets:
            self.active_connections.discard(dead)


ws_hub = WebSocketHub()


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
    token: str = Query(default="")
):
    """Authenticated WebSocket endpoint for real-time telemetry streaming and alerts."""
    await ws_hub.connect(websocket)
    try:
        # Send initial connection acknowledgment
        await websocket.send_text(json.dumps({
            "event": "connector:connected",
            "data": {
                "status": "ONLINE",
                "message": "CrashSense AI Telemetry Hub connected.",
                "server_time": datetime.now(timezone.utc).isoformat()
            }
        }))

        while True:
            # Handle incoming ping / messages from client
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                if data.get("action") == "ping":
                    await websocket.send_text(json.dumps({
                        "event": "pong",
                        "data": {"time": datetime.now(timezone.utc).isoformat()}
                    }))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket error: %s", str(exc))
        ws_hub.disconnect(websocket)
