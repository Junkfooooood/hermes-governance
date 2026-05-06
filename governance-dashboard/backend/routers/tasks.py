"""GET /api/tasks — task list and detail with sub-task tree."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

_bridge = None
_task_index = None
_event_bus = None


def init(bridge, task_index, event_bus):
    global _bridge, _task_index, _event_bus
    _bridge = bridge
    _task_index = task_index
    _event_bus = event_bus


@router.get("/api/tasks")
async def list_tasks(
    state: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = Query("updated_at", pattern="^(updated_at|created_at|sub_task_count)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    tasks, total = _task_index.query(
        state=state, search=search, sort=sort, limit=limit, offset=offset
    )
    # Enrich each task with sub-task details from full transaction data
    enriched = []
    for task in tasks:
        txn = _bridge.load_transaction(task["txn_id"])
        if txn:
            task["sub_tasks"] = txn.get("sub_tasks", [])
            task["contracts"] = txn.get("contracts", [])
            task["results"] = txn.get("results", [])
            # Count sub-task statuses
            results = txn.get("results", [])
            completed = sum(1 for r in results if r.get("status") == "completed")
            failed = sum(1 for r in results if r.get("status") == "failed")
            task["sub_task_progress"] = {
                "completed": completed,
                "failed": failed,
                "pending": max(0, len(task["sub_tasks"]) - completed - failed),
            }
            # Active agents in this task
            active_roles = set()
            for c in txn.get("contracts", []):
                active_roles.add(c.get("ministry", ""))
            task["involved_roles"] = list(active_roles)
        enriched.append(task)
    return {"tasks": enriched, "total": total, "limit": limit, "offset": offset}


@router.get("/api/tasks/{txn_id}")
async def get_task(txn_id: str):
    txn = _bridge.load_transaction(txn_id)
    if not txn:
        raise HTTPException(
            status_code=404,
            detail={"code": "TASK_NOT_FOUND", "message": f"Task {txn_id} not found"},
        )
    # Enrich with agent context for each sub-task
    contracts = txn.get("contracts", [])
    results = txn.get("results", [])
    sub_tasks = txn.get("sub_tasks", [])

    # Build agent activity map per sub-task
    for st in sub_tasks:
        st_id = st.get("id", "")
        ministry = st.get("ministry", "")
        st["agent_activity"] = {
            "role": ministry,
            "contract": None,
            "result": None,
        }
        for c in contracts:
            if c.get("ministry") == ministry:
                st["agent_activity"]["contract"] = {
                    "delegation_id": c.get("delegation_id", ""),
                    "authority": c.get("authority", []),
                    "deadline": c.get("deadline", ""),
                }
                break
        for r in results:
            if r.get("ministry") == ministry:
                st["agent_activity"]["result"] = {
                    "status": r.get("status", ""),
                    "summary": str(r.get("result", ""))[:300] if r.get("result") else "",
                    "error": r.get("error"),
                }
                break

    txn["sub_tasks"] = sub_tasks
    return txn


@router.get("/api/tasks/{txn_id}/audit")
async def get_task_audit(txn_id: str):
    txn = _bridge.load_transaction(txn_id)
    if not txn:
        raise HTTPException(
            status_code=404,
            detail={"code": "TASK_NOT_FOUND", "message": f"Task {txn_id} not found"},
        )
    events = _event_bus.get_events_for_txn(txn_id)
    return {
        "audit_trail": txn.get("audit_trail", []),
        "events": events,
    }
