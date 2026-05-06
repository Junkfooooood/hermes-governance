"""GET/POST /api/alerts — alert list and lifecycle management."""

from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()

_bridge = None
_task_index = None
_alert_engine = None


def init(bridge, task_index):
    global _bridge, _task_index, _alert_engine
    _bridge = bridge
    _task_index = task_index
    from services.alert_engine import AlertEngine
    from config import STATE_DIR
    _alert_engine = AlertEngine(STATE_DIR)


@router.get("/api/alerts")
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    since: Optional[str] = None,
):
    alerts = _alert_engine.get_alerts(status=status, severity=severity, since=since)
    return {"alerts": alerts}


@router.post("/api/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    if _alert_engine.acknowledge(alert_id):
        return {"status": "acknowledged"}
    raise HTTPException(status_code=404, detail={"code": "ALERT_NOT_FOUND", "message": f"Alert {alert_id} not found"})


@router.post("/api/alerts/{alert_id}/suppress")
async def suppress_alert(alert_id: str, until: str = ""):
    if not until:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PARAMS", "message": "until parameter required"})
    if _alert_engine.suppress(alert_id, until):
        return {"status": "suppressed"}
    raise HTTPException(status_code=404, detail={"code": "ALERT_NOT_FOUND", "message": f"Alert {alert_id} not found"})
