"""WebSocket broadcast for live auction updates.

Design (ponytail: simplest approach):
- REST endpoint handles bid placement (with all validation).
- WS only broadcasts updates to connected clients per auction room.
- No race condition risk — REST handles concurrency.
"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # auction_id -> set of WebSocket connections
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, auction_id: str):
        await websocket.accept()
        if auction_id not in self.active_connections:
            self.active_connections[auction_id] = set()
        self.active_connections[auction_id].add(websocket)

    def disconnect(self, websocket: WebSocket, auction_id: str):
        room = self.active_connections.get(auction_id)
        if room:
            room.discard(websocket)
            if not room:
                del self.active_connections[auction_id]

    async def broadcast(self, auction_id: str, message: dict):
        """Send a JSON message to all clients in an auction room."""
        room = self.active_connections.get(auction_id)
        if not room:
            return
        payload = json.dumps(message)
        stale = set()
        for ws in room:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.add(ws)
        # Clean up dead connections
        for ws in stale:
            room.discard(ws)
        if not room:
            del self.active_connections[auction_id]


manager = ConnectionManager()


@ws_router.websocket("/ws/auctions/{auction_id}")
async def auction_websocket(
    websocket: WebSocket,
    auction_id: str,
    token: str = Query(...),
):
    """Connect to live auction updates. Requires a valid JWT as query param."""
    # Authenticate via token query param
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await manager.connect(websocket, auction_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "auction_id": auction_id,
            "user_id": user_id,
        })

        # Keep connection alive until client disconnects
        while True:
            # We don't expect messages from client (bid via REST only)
            # but we need to keep the connection open and handle pings
            data = await websocket.receive_text()
            # Client could send heartbeat — ignore everything
            pass
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, auction_id)