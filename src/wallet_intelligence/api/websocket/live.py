"""WebSocket live transaction stream."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Global subscribers list
_subscribers: list[asyncio.Queue] = []


def get_subscribers() -> list[asyncio.Queue]:
    """Get all WebSocket subscribers."""
    return _subscribers


async def broadcast(event: dict) -> None:
    """Broadcast event to all WebSocket clients."""
    for queue in _subscribers:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """WebSocket endpoint for real-time transaction stream."""
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.append(queue)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"event": "heartbeat"})
            except WebSocketDisconnect:
                break
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)
