"""GET /api/audit/transactions — audit replay data."""

from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()

_bridge = None
_event_bus = None


def init(bridge, event_bus):
    global _bridge, _event_bus
    _bridge = bridge
    _event_bus = event_bus


@router.get("/api/audit/transactions")
async def list_audit_transactions(
    state: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    transactions = _bridge.load_all_transactions()

    # Filter
    if state:
        transactions = [t for t in transactions if t.get("state") == state]
    if since:
        transactions = [t for t in transactions if t.get("updated_at", "") >= since]

    # Sort by updated_at desc
    transactions.sort(key=lambda t: t.get("updated_at", ""), reverse=True)

    return {"transactions": transactions[:limit]}
