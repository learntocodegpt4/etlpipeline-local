"""WebSocket routes for real-time log streaming"""

import asyncio
import json
from typing import Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(
            "websocket_connected",
            connections=len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection"""
        self.active_connections.discard(websocket)
        logger.info(
            "websocket_disconnected",
            connections=len(self.active_connections),
        )

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connections"""
        if not self.active_connections:
            return

        message_json = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.add(connection)

        # Remove disconnected
        for conn in disconnected:
            self.active_connections.discard(conn)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time log streaming"""
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to log stream",
        })

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (e.g., ping/pong)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,
                )

                # Handle ping
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)


async def broadcast_log(
    level: str,
    message: str,
    job_id: str | None = None,
    step: str | None = None,
    details: dict | None = None,
) -> None:
    """Broadcast log message to all connected clients"""
    await manager.broadcast({
        "type": "log",
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        "job_id": job_id,
        "step": step,
        "details": details or {},
    })


async def broadcast_job_event(
    event: str,
    job_id: str,
    status: str | None = None,
    details: dict | None = None,
) -> None:
    """Broadcast job event to all connected clients"""
    await manager.broadcast({
        "type": "job_event",
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "job_id": job_id,
        "status": status,
        "details": details or {},
    })
