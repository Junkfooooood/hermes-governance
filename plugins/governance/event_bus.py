"""Governance event bus — shared module for event emission and persistence.

Imported by:
- Governance plugin (producer): emits events during state transitions
- Dashboard backend (consumer): tails events.jsonl for real-time updates
"""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class GovernanceEventBus:
    """In-process event bus with JSONL persistence.

    Thread-safe for producers (sync), async for consumers.
    """

    def __init__(self, events_file: Optional[Path] = None):
        self._events_file = events_file
        self._global_seq: int = 0
        self._txn_seqs: Dict[str, int] = {}
        self._recent_events: List[dict] = []
        self._max_recent = 1000
        self._lock = threading.Lock()

    def emit(self, txn_id: str, event_type: str, payload: dict) -> dict:
        """Emit an event. Thread-safe. Returns the event dict."""
        with self._lock:
            self._global_seq += 1
            self._txn_seqs[txn_id] = self._txn_seqs.get(txn_id, 0) + 1
            event = {
                "event_id": f"evt_{uuid4().hex[:8]}",
                "global_seq": self._global_seq,
                "txn_id": txn_id,
                "txn_seq": self._txn_seqs[txn_id],
                "type": event_type,
                "payload": payload,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            # Persist to JSONL
            if self._events_file:
                self._append_jsonl(event)
            # Ring buffer
            self._recent_events.append(event)
            if len(self._recent_events) > self._max_recent:
                self._recent_events = self._recent_events[-self._max_recent :]
        return event

    def get_events_after_seq(self, seq: int) -> List[dict]:
        """Get events after a given global_seq (for reconnection)."""
        with self._lock:
            return [e for e in self._recent_events if e["global_seq"] > seq]

    def get_events_for_txn(self, txn_id: str) -> List[dict]:
        """Get all recent events for a specific transaction."""
        with self._lock:
            return [e for e in self._recent_events if e["txn_id"] == txn_id]

    def _append_jsonl(self, event: dict) -> None:
        """Append event to JSONL file."""
        if not self._events_file:
            return
        try:
            self._events_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._events_file, "a") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"Failed to append event to {self._events_file}: {e}")


# Module-level singleton
_bus: Optional[GovernanceEventBus] = None
_lock = threading.Lock()

_DEFAULT_EVENTS_FILE = Path.home() / ".hermes" / "governance" / "state" / "events.jsonl"


def get_bus(events_file: Optional[Path] = None) -> GovernanceEventBus:
    """Get or create the singleton event bus."""
    global _bus
    if _bus is None:
        with _lock:
            if _bus is None:
                _bus = GovernanceEventBus(events_file=events_file or _DEFAULT_EVENTS_FILE)
    return _bus
