"""GET/POST/PATCH /api/annotations — annotation CRUD."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

router = APIRouter()

_bridge = None


def init(bridge):
    global _bridge
    _bridge = bridge


@router.get("/api/annotations")
async def list_annotations(
    txn_id: Optional[str] = None,
    include_deleted: bool = False,
):
    annotations = _bridge.load_annotations(txn_id=txn_id, include_deleted=include_deleted)
    return {"annotations": annotations}


@router.post("/api/annotations")
async def create_annotation(body: dict):
    txn_id = body.get("txn_id")
    content = body.get("content")
    if not txn_id or not content:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PARAMS", "message": "txn_id and content required"},
        )
    now = datetime.now(timezone.utc).isoformat()
    annotation = {
        "annotation_id": f"ann_{uuid4().hex[:8]}",
        "txn_id": txn_id,
        "event_index": body.get("event_index", 0),
        "content": content,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }
    _bridge.save_annotation(annotation)
    return annotation


@router.patch("/api/annotations/{annotation_id}")
async def update_annotation(annotation_id: str, body: dict):
    updates = {}
    if "content" in body:
        updates["content"] = body["content"]
    if "status" in body:
        valid = {"pending", "confirmed", "fixed", "ignored"}
        if body["status"] not in valid:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_PARAMS", "message": f"status must be one of {valid}"},
            )
        updates["status"] = body["status"]
    if "deleted" in body:
        updates["deleted"] = body["deleted"]

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    if _bridge.update_annotation(annotation_id, updates):
        return {"status": "updated"}
    raise HTTPException(
        status_code=404,
        detail={"code": "ANNOTATION_NOT_FOUND", "message": f"Annotation {annotation_id} not found"},
    )
