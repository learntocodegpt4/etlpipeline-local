"""WebSocket routes for real-time log streaming."""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.orchestrator.state_manager import StateManager

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for log streaming."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store a new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time log streaming.

    Clients can subscribe to:
    - All logs
    - Logs for a specific job_id

    Message format from client:
    {
        "type": "subscribe",
        "job_id": "optional_job_id"
    }
    """
    await manager.connect(websocket)
    state_manager = StateManager()

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to log stream",
        })

        job_id_filter: str | None = None
        last_check: datetime = datetime.now()

        while True:
            try:
                # Check for client messages (non-blocking)
                try:
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=1.0,
                    )
                    message = json.loads(data)

                    if message.get("type") == "subscribe":
                        job_id_filter = message.get("job_id")
                        await websocket.send_json({
                            "type": "subscribed",
                            "job_id": job_id_filter,
                            "timestamp": datetime.now().isoformat(),
                        })
                    elif message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat(),
                        })

                except TimeoutError:
                    pass

                # Poll for new job updates every 2 seconds
                if (datetime.now() - last_check).total_seconds() >= 2:
                    # Get recent jobs
                    jobs = await state_manager.get_jobs(limit=10)

                    for job in jobs:
                        # Filter by job_id if specified
                        if job_id_filter and job["job_id"] != job_id_filter:
                            continue

                        # Send job status updates
                        if job["status"] in ("running", "success", "failed"):
                            await websocket.send_json({
                                "type": "job_update",
                                "timestamp": datetime.now().isoformat(),
                                "job": {
                                    "job_id": job["job_id"],
                                    "status": job["status"],
                                    "pipeline_name": job["pipeline_name"],
                                    "total_records": job["total_records"],
                                    "error_message": job.get("error_message"),
                                },
                            })

                            # Get and send job details if running or just completed
                            if job["status"] in ("running", "success", "failed"):
                                details = await state_manager.get_job_details(job["job_id"])
                                for detail in details:
                                    await websocket.send_json({
                                        "type": "log",
                                        "timestamp": datetime.now().isoformat(),
                                        "job_id": job["job_id"],
                                        "step": detail["step_name"],
                                        "step_type": detail["step_type"],
                                        "status": detail["status"],
                                        "records": detail["records_processed"],
                                        "error": detail.get("error_message"),
                                    })

                    last_check = datetime.now()

            except WebSocketDisconnect:
                break

    except Exception:
        pass
    finally:
        manager.disconnect(websocket)


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_logs(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for streaming logs of a specific job.

    Args:
        websocket: WebSocket connection
        job_id: Job ID to stream logs for
    """
    await manager.connect(websocket)
    state_manager = StateManager()

    try:
        # Send initial job status
        job = await state_manager.get_job(job_id)
        if job:
            await websocket.send_json({
                "type": "job_status",
                "timestamp": datetime.now().isoformat(),
                "job": job,
            })

            # Send existing details
            details = await state_manager.get_job_details(job_id)
            for detail in details:
                await websocket.send_json({
                    "type": "log",
                    "timestamp": datetime.now().isoformat(),
                    "detail": detail,
                })
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Job {job_id} not found",
            })
            return

        # Poll for updates while job is running
        while True:
            try:
                await asyncio.sleep(2)

                job = await state_manager.get_job(job_id)
                if not job:
                    break

                await websocket.send_json({
                    "type": "job_status",
                    "timestamp": datetime.now().isoformat(),
                    "job": job,
                })

                # Check if job is complete
                if job["status"] in ("success", "failed"):
                    # Send final details
                    details = await state_manager.get_job_details(job_id)
                    await websocket.send_json({
                        "type": "job_complete",
                        "timestamp": datetime.now().isoformat(),
                        "job": job,
                        "details": details,
                    })
                    break

            except WebSocketDisconnect:
                break

    except Exception:
        pass
    finally:
        manager.disconnect(websocket)
