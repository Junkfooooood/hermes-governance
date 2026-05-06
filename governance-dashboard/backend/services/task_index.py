"""In-memory task index — disposable cache backed by transaction files.

Rebuilt from files on startup, updated by events at runtime.
Async flush to index.json every 30s or 50 events.
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TaskSummary:
    txn_id: str
    goal: str
    state: str
    priority: str
    created_at: str
    updated_at: str
    created_at_ts: float  # epoch for sorting
    updated_at_ts: float
    sub_task_count: int
    review_verdict: Optional[str] = None


class TaskIndex:
    _SORT_FIELDS = {
        "updated_at": ("updated_at_ts", True),  # desc
        "created_at": ("created_at_ts", True),  # desc
        "sub_task_count": ("sub_task_count", True),
    }

    def __init__(self, state_dir: Path, bridge=None):
        self._state_dir = state_dir
        self._bridge = bridge
        self._index_path = state_dir / "index.json"
        self._tasks: Dict[str, TaskSummary] = {}
        self._global_seq: int = 0
        self._dirty_count = 0
        self._dirty_since: float = 0

    def rebuild_from_files(self) -> None:
        """Startup: scan all transaction files, rebuild index."""
        if not self._bridge:
            return
        transactions = self._bridge.load_all_transactions()
        for raw in transactions:
            txn_id = raw.get("txn_id", "")
            if txn_id:
                self._tasks[txn_id] = self._extract_summary(raw)
        logger.info(f"TaskIndex rebuilt: {len(self._tasks)} transactions")

    def on_event(self, event: dict) -> None:
        """Event-driven update. Zero file I/O during normal operation."""
        seq = event.get("global_seq", 0)
        if seq <= self._global_seq:
            return  # dedup
        self._global_seq = seq

        etype = event.get("type", "")
        txn_id = event.get("txn_id", "")
        payload = event.get("payload", {})

        if etype == "state.transition" and txn_id in self._tasks:
            self._tasks[txn_id].state = payload.get(
                "state", self._tasks[txn_id].state
            )
            self._tasks[txn_id].updated_at = event.get("created_at", "")
            try:
                self._tasks[txn_id].updated_at_ts = datetime.fromisoformat(
                    event["created_at"].replace("Z", "+00:00")
                ).timestamp()
            except (KeyError, ValueError):
                pass
        elif etype == "transaction.created":
            # Refresh from file if available
            if self._bridge:
                txn = self._bridge.load_transaction(txn_id)
                if txn and txn_id not in self._tasks:
                    self._tasks[txn_id] = self._extract_summary(txn)

        self._dirty_count += 1
        if self._dirty_since == 0:
            self._dirty_since = time.time()
        self._maybe_flush()

    def query(
        self,
        state: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "updated_at",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[dict], int]:
        """Query with filtering, search, sorting, pagination."""
        field, desc = self._SORT_FIELDS.get(sort, ("updated_at_ts", True))
        results = list(self._tasks.values())
        if state:
            results = [t for t in results if t.state == state]
        if search:
            q = search.lower()
            results = [
                t for t in results if q in t.goal.lower() or q in t.txn_id.lower()
            ]
        results.sort(key=lambda t: getattr(t, field, 0), reverse=desc)
        total = len(results)
        page = results[offset : offset + limit]
        return [asdict(t) for t in page], total

    def get_stats(self) -> dict:
        """Aggregate statistics for overview."""
        by_state: Dict[str, int] = {}
        for t in self._tasks.values():
            by_state[t.state] = by_state.get(t.state, 0) + 1

        terminal = {"complete", "rejected", "error"}
        active_count = sum(
            1 for t in self._tasks.values() if t.state not in terminal
        )
        error_count = by_state.get("error", 0)
        completed_count = by_state.get("complete", 0)

        # Recent 5 transactions
        recent = sorted(
            self._tasks.values(), key=lambda t: t.updated_at_ts, reverse=True
        )[:5]

        return {
            "total": len(self._tasks),
            "by_state": by_state,
            "active_count": active_count,
            "error_count": error_count,
            "completed_count": completed_count,
            "recent": [asdict(t) for t in recent],
        }

    def _extract_summary(self, raw: dict) -> TaskSummary:
        """Extract TaskSummary from a raw transaction dict."""
        created_at = raw.get("created_at", "")
        updated_at = raw.get("updated_at", "")
        return TaskSummary(
            txn_id=raw.get("txn_id", ""),
            goal=raw.get("goal", ""),
            state=raw.get("state", ""),
            priority=raw.get("priority", "normal"),
            created_at=created_at,
            updated_at=updated_at,
            created_at_ts=self._parse_ts(created_at),
            updated_at_ts=self._parse_ts(updated_at),
            sub_task_count=len(raw.get("sub_tasks", [])),
            review_verdict=raw.get("review_verdict"),
        )

    @staticmethod
    def _parse_ts(iso_str: str) -> float:
        """Parse ISO8601 string to epoch float."""
        if not iso_str:
            return 0.0
        try:
            return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0

    def _maybe_flush(self) -> None:
        """Async flush: every 30s or every 50 events."""
        now = time.time()
        if self._dirty_count >= 50 or (
            self._dirty_since and now - self._dirty_since > 30
        ):
            self.flush_to_disk()
            self._dirty_count = 0
            self._dirty_since = 0

    def flush_to_disk(self) -> None:
        """Atomic write: .tmp -> os.replace(). Failure only logs warning."""
        try:
            data = {
                "global_seq": self._global_seq,
                "tasks": {k: asdict(v) for k, v in self._tasks.items()},
            }
            tmp = self._index_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False))
            tmp.replace(self._index_path)
        except OSError as e:
            logger.warning(f"Failed to flush index: {e}")
