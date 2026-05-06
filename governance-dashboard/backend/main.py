"""Governance Dashboard — FastAPI backend."""

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import PORT, STATE_DIR
from routers import alerts, annotations, agents, audit, events, overview, pipeline, tasks, workflow
from services.event_bus import DashboardEventBus
from services.governance_bridge import GovernanceBridge
from services.task_index import TaskIndex

# Shared service instances
bridge = GovernanceBridge(STATE_DIR)
task_index = TaskIndex(STATE_DIR, bridge)
event_bus = DashboardEventBus(STATE_DIR / "events.jsonl")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: rebuild index from files, start event file tailer
    task_index.rebuild_from_files()
    await event_bus.start()
    yield
    # Shutdown: flush index, stop event tailer
    task_index.flush_to_disk()
    await event_bus.stop()


app = FastAPI(title="Governance Dashboard", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Unified response middleware
@app.middleware("http")
async def wrap_response(request: Request, call_next):
    # Skip WebSocket and static file requests
    if request.url.path.startswith("/ws/") or request.url.path.startswith("/assets/"):
        return await call_next(request)

    response = await call_next(request)

    # Only wrap JSON responses from /api/ endpoints
    if not request.url.path.startswith("/api/"):
        return response

    # Read response body
    body = b""
    async for chunk in response.body_iterator:
        body += chunk if isinstance(chunk, bytes) else chunk.encode()

    request_id = f"req_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    meta = {"request_id": request_id, "timestamp": timestamp}

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return response

    # Error responses (4xx/5xx) — wrap as {error, meta}
    if response.status_code >= 400:
        if isinstance(data, dict) and "error" in data:
            wrapped = {"error": data["error"], "meta": meta}
        elif isinstance(data, dict) and "detail" in data:
            detail = data["detail"]
            if isinstance(detail, dict):
                wrapped = {"error": detail, "meta": meta}
            else:
                wrapped = {
                    "error": {"code": "ERROR", "message": str(detail)},
                    "meta": meta,
                }
        else:
            wrapped = {
                "error": {"code": "ERROR", "message": str(data)},
                "meta": meta,
            }
        return JSONResponse(content=wrapped, status_code=response.status_code)

    # Success responses — wrap as {data, meta}
    return JSONResponse(content={"data": data, "meta": meta}, status_code=200)


# Wire services into routers
overview.init(bridge, task_index, event_bus)
tasks.init(bridge, task_index, event_bus)
agents.init(bridge, task_index)
pipeline.init()
alerts.init(bridge, task_index)
audit.init(bridge, event_bus)
annotations.init(bridge)
events.init(event_bus)
workflow.init(bridge)

# Include routers
app.include_router(overview.router)
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(pipeline.router)
app.include_router(alerts.router)
app.include_router(audit.router)
app.include_router(annotations.router)
app.include_router(events.router)
app.include_router(workflow.router)

# Serve frontend static files
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Serve static assets directly
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # SPA catch-all: serve index.html for all non-API, non-asset routes
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Try to serve the exact file first
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fall back to index.html for SPA routing
        return FileResponse(str(frontend_dist / "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
