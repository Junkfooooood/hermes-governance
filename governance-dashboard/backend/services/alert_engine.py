"""Alert engine — evaluates rules against current state, manages alert lifecycle."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


ALERT_RULES = [
    {
        "id": "alert.task_error",
        "severity": "critical",
        "description": "任务执行失败",
    },
    {
        "id": "alert.task_timeout",
        "severity": "warning",
        "description": "任务超时",
    },
    {
        "id": "alert.task_stuck",
        "severity": "warning",
        "description": "任务卡住超过10分钟",
    },
    {
        "id": "alert.rule_violation",
        "severity": "high",
        "description": "规则违反",
    },
    {
        "id": "alert.verify_failed",
        "severity": "high",
        "description": "验证失败",
    },
]


class AlertEngine:
    def __init__(self, state_dir: Path):
        self._state_dir = state_dir
        self._alerts_path = state_dir / "alerts.jsonl"
        self._alert_state_path = state_dir / "alert_state.json"

    def evaluate(self, tasks: list, feedback_entries: list) -> List[dict]:
        """Run alert rules against current state. Returns new alerts."""
        now = datetime.now(timezone.utc)
        new_alerts = []

        for task in tasks:
            state = task.get("state", "")
            txn_id = task.get("txn_id", task.get("transaction_id", ""))

            # alert.task_error
            if state == "error":
                new_alerts.append(
                    self._make_alert(
                        "alert.task_error", "critical", txn_id,
                        f"任务 {txn_id} 执行失败", now,
                    )
                )

            # alert.task_stuck (updated_at + 10min < now, non-terminal)
            terminal = {"complete", "rejected", "error"}
            if state not in terminal:
                updated_at = task.get("updated_at", "")
                if updated_at:
                    try:
                        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        if (now - updated).total_seconds() > 600:
                            new_alerts.append(
                                self._make_alert(
                                    "alert.task_stuck", "warning", txn_id,
                                    f"任务 {txn_id} 已超过10分钟未更新", now,
                                )
                            )
                    except ValueError:
                        pass

            # alert.verify_failed
            verify = task.get("verify_result")
            if verify and isinstance(verify, dict) and not verify.get("passed", True):
                new_alerts.append(
                    self._make_alert(
                        "alert.verify_failed", "high", txn_id,
                        f"任务 {txn_id} 验证失败", now,
                    )
                )

        # alert.rule_violation from feedback
        for fb in feedback_entries:
            if fb.get("type") == "violation":
                txn_id = fb.get("transaction_id", "")
                new_alerts.append(
                    self._make_alert(
                        "alert.rule_violation", "high", txn_id,
                        f"规则违反: {fb.get('detail', 'unknown')}", now,
                    )
                )

        # Persist new alerts
        for alert in new_alerts:
            self._append_alert(alert)

        return new_alerts

    def get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[str] = None,
    ) -> List[dict]:
        """Get alerts merged with processing state."""
        alerts = self._load_alerts()
        alert_state = self._load_alert_state()
        now = datetime.now(timezone.utc)

        merged = []
        for alert in alerts:
            aid = alert.get("alert_id", "")
            state = alert_state.get(aid, {"status": "active"})

            # Dynamic suppressed_until evaluation
            if state.get("status") == "suppressed":
                suppressed_until = state.get("suppressed_until")
                if suppressed_until:
                    try:
                        until_dt = datetime.fromisoformat(suppressed_until.replace("Z", "+00:00"))
                        if now > until_dt:
                            state["status"] = "active"
                    except ValueError:
                        pass

            alert["status"] = state.get("status", "active")
            alert["acknowledged_by"] = state.get("acknowledged_by")
            alert["acknowledged_at"] = state.get("acknowledged_at")
            alert["suppressed_until"] = state.get("suppressed_until")
            alert["resolved_at"] = state.get("resolved_at")

            # Filters
            if status and alert["status"] != status:
                continue
            if severity and alert.get("severity") != severity:
                continue
            if since:
                try:
                    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                    alert_dt = datetime.fromisoformat(alert["triggered_at"].replace("Z", "+00:00"))
                    if alert_dt < since_dt:
                        continue
                except (ValueError, KeyError):
                    pass

            merged.append(alert)

        return merged

    def acknowledge(self, alert_id: str, by: str = "user") -> bool:
        """Acknowledge an alert."""
        state = self._load_alert_state()
        if alert_id not in state:
            state[alert_id] = {"status": "active"}
        current = state[alert_id].get("status", "active")
        if current == "resolved":
            return False
        state[alert_id]["status"] = "acknowledged"
        state[alert_id]["acknowledged_by"] = by
        state[alert_id]["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
        self._save_alert_state(state)
        return True

    def suppress(self, alert_id: str, until: str) -> bool:
        """Suppress an alert until a given time."""
        state = self._load_alert_state()
        if alert_id not in state:
            state[alert_id] = {"status": "active"}
        if state[alert_id].get("status") == "resolved":
            return False
        state[alert_id]["status"] = "suppressed"
        state[alert_id]["suppressed_until"] = until
        self._save_alert_state(state)
        return True

    def _make_alert(
        self, rule_id: str, severity: str, txn_id: str, message: str, now: datetime
    ) -> dict:
        return {
            "alert_id": f"alt_{uuid4().hex[:8]}",
            "rule_id": rule_id,
            "severity": severity,
            "txn_id": txn_id,
            "message": message,
            "triggered_at": now.isoformat(),
        }

    def _append_alert(self, alert: dict) -> None:
        try:
            self._alerts_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._alerts_path, "a") as f:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"Failed to append alert: {e}")

    def _load_alerts(self) -> List[dict]:
        if not self._alerts_path.exists():
            return []
        results = []
        try:
            for line in self._alerts_path.read_text().strip().splitlines():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
        return results

    def _load_alert_state(self) -> Dict[str, dict]:
        if not self._alert_state_path.exists():
            return {}
        try:
            return json.loads(self._alert_state_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_alert_state(self, state: Dict[str, dict]) -> None:
        tmp = self._alert_state_path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            tmp.replace(self._alert_state_path)
        except OSError as e:
            logger.warning(f"Failed to save alert state: {e}")
