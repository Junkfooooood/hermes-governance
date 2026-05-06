"""WS /ws/events — real-time event streaming via WebSocket."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

_event_bus = None


def init(event_bus):
    global _event_bus
    _event_bus = event_bus


@router.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()

    # Phase 1: Client sends subscription message with last_global_seq
    try:
        msg = await ws.receive_json()
    except Exception:
        msg = {}

    last_seq = msg.get("last_global_seq", 0)

    # Phase 2: Replay missed events
    if last_seq > 0:
        missed = _event_bus.get_events_after_seq(last_seq)
        for e in missed:
            await ws.send_text(json.dumps(e, ensure_ascii=False))

    # Phase 3: Subscribe to real-time stream
    queue = await _event_bus.subscribe()
    try:
        while True:
            event = await queue.get()
            await ws.send_text(json.dumps(event, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    finally:
        _event_bus.unsubscribe(queue)
