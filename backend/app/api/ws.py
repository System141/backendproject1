"""WebSocket broadcast for live auction updates.

Design (ponytail: simplest approach):
- REST endpoint handles bid placement (with all validation).
- WS only broadcasts updates to connected clients per auction room.
- No race condition risk — REST handles concurrency.
- Heartbeat every 30s to detect stale connections.
"""
import json
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.core.security import decode_access_token
from app.core.database import AsyncSessionLocal
from app.models.domain import User

AUTH_TIMEOUT_SECONDS = 5

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # auction_id -> dict of {websocket: user_id}
        self.active_connections: dict[str, dict[str, set[WebSocket]]] = {}
        self.connection_metadata: dict[WebSocket, tuple[str, int, int]] = {}
        self._heartbeat_task: asyncio.Task | None = None

    async def _heartbeat(self):
        """Periodically ping all connections to detect stale ones."""
        while True:
            await asyncio.sleep(30)
            now = int(datetime.now(timezone.utc).timestamp())
            for auction_id, rooms in list(self.active_connections.items()):
                connections = rooms.get("connections", set())
                user_ids = {
                    self.connection_metadata[ws][0]
                    for ws in connections
                    if ws in self.connection_metadata
                }
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(User.id, User.auth_version, User.status).where(User.id.in_(user_ids))
                    )
                    users = {row.id: row for row in result.all()}
                stale = set()
                for ws in list(connections):
                    metadata = self.connection_metadata.get(ws)
                    user = users.get(metadata[0]) if metadata else None
                    invalid = (
                        metadata is None
                        or metadata[2] <= now
                        or user is None
                        or user.status != "active"
                        or user.auth_version != metadata[1]
                    )
                    try:
                        if invalid:
                            await ws.close(code=4003, reason="Session expired")
                        else:
                            await ws.send_json({"type": "ping"})
                    except Exception:
                        pass
                    if invalid:
                        stale.add(ws)
                for ws in stale:
                    rooms["connections"].discard(ws)
                    self.connection_metadata.pop(ws, None)
                if not rooms["connections"]:
                    self.active_connections.pop(auction_id, None)

    async def start_heartbeat(self):
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def connect(self, websocket: WebSocket, auction_id: str, user_id: str, auth_version: int, expires_at: int):
        # Caller (auction_websocket) already accepted the socket - it has to,
        # to receive the first-message auth payload before this is called.
        if auction_id not in self.active_connections:
            self.active_connections[auction_id] = {"connections": set(), "user_ids": set()}
        self.active_connections[auction_id]["connections"].add(websocket)
        self.active_connections[auction_id]["user_ids"].add(user_id)
        self.connection_metadata[websocket] = (user_id, auth_version, expires_at)
        await self._broadcast_user_count(auction_id)

    def disconnect(self, websocket: WebSocket, auction_id: str):
        room = self.active_connections.get(auction_id)
        if room:
            room["connections"].discard(websocket)
            metadata = self.connection_metadata.pop(websocket, None)
            if metadata:
                room["user_ids"].discard(metadata[0])
            if not room["connections"]:
                self.active_connections.pop(auction_id, None)
            else:
                asyncio.create_task(self._broadcast_user_count(auction_id))

    async def disconnect_user(self, user_id: str):
        """Close all sockets for a user after an authentication change."""
        for auction_id, room in list(self.active_connections.items()):
            targets = [
                ws for ws in list(room["connections"])
                if self.connection_metadata.get(ws, (None, 0, 0))[0] == user_id
            ]
            for ws in targets:
                try:
                    await ws.close(code=4003, reason="Session revoked")
                except Exception:
                    pass
                self.disconnect(ws, auction_id)

    async def _broadcast_user_count(self, auction_id: str):
        room = self.active_connections.get(auction_id)
        if room:
            await self.broadcast(auction_id, {
                "type": "user_count",
                "count": len(room["connections"]),
            })

    async def broadcast(self, auction_id: str, message: dict):
        """Send a JSON message to all clients in an auction room."""
        room = self.active_connections.get(auction_id)
        if not room:
            return
        payload = json.dumps(message)
        stale = set()
        for ws in room["connections"]:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.add(ws)
        for ws in stale:
            room["connections"].discard(ws)
            self.connection_metadata.pop(ws, None)
        if not room["connections"]:
            self.active_connections.pop(auction_id, None)

    def get_online_count(self, auction_id: str) -> int:
        room = self.active_connections.get(auction_id)
        return len(room["connections"]) if room else 0


manager = ConnectionManager()


@ws_router.websocket("/ws/auctions/{auction_id}")
async def auction_websocket(
    websocket: WebSocket,
    auction_id: str,
):
    """Connect to live auction updates. Security review: the JWT used to
    ride in the `?token=` query string, which lands in cleartext in server/
    proxy access logs on every connect. Instead, accept the socket and
    require the client's first message to be {"type":"auth","token":"..."}
    within AUTH_TIMEOUT_SECONDS - same secret, never written to a URL."""
    await websocket.accept()
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=AUTH_TIMEOUT_SECONDS)
        msg = json.loads(raw)
    except (asyncio.TimeoutError, json.JSONDecodeError, WebSocketDisconnect):
        await websocket.close(code=4001, reason="Auth timeout")
        return

    if msg.get("type") != "auth" or not msg.get("token"):
        await websocket.close(code=4001, reason="First message must be {type: 'auth', token: ...}")
        return

    payload = decode_access_token(msg["token"])
    if payload is None:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    user_id = payload.get("sub")
    token_version = payload.get("ver")
    expires_at = payload.get("exp")
    if not user_id or token_version is None or not isinstance(expires_at, int):
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
    if user is None or user.status != "active" or user.auth_version != token_version:
        await websocket.close(code=4003, reason="Session revoked")
        return

    await manager.connect(websocket, auction_id, user_id, token_version, expires_at)

    try:
        # Send initial connection confirmation with online count
        online_count = manager.get_online_count(auction_id)
        await websocket.send_json({
            "type": "connected",
            "auction_id": auction_id,
            "user_id": user_id,
            "online_count": online_count,
        })

        # Keep connection alive until client disconnects
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            # Handle client pong
            if msg.get("type") == "pong":
                continue
            # Handle ping
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
    except (WebSocketDisconnect, json.JSONDecodeError):
        pass
    finally:
        manager.disconnect(websocket, auction_id)
