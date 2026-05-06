"""GET /api/overview — aggregate statistics."""

from fastapi import APIRouter

router = APIRouter()

_bridge = None
_task_index = None
_event_bus = None


def init(bridge, task_index, event_bus):
    global _bridge, _task_index, _event_bus
    _bridge = bridge
    _task_index = task_index
    _event_bus = event_bus


@router.get("/api/overview")
async def get_overview():
    stats = _task_index.get_stats()
    agents = _bridge.load_all_agents()
    return {
        "total_transactions": stats["total"],
        "by_state": stats["by_state"],
        "active_count": stats["active_count"],
        "error_count": stats["error_count"],
        "completed_count": stats["completed_count"],
        "recent_transactions": stats["recent"],
        "agent_summary": agents,
    }
