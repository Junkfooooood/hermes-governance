"""Dashboard-side event bus — tails governance events.jsonl for real-time updates."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardEventBus:
    """Tails events.jsonl and provides async queue subscriptions for WebSocket streaming."""

    def __init__(self, events_file: Path):
        self._events_file = events_file
        self._subscribers: List[asyncio.Queue] = []
        self._recent_events: List[dict] = []
        self._max_recent = 1000
        self._tail_task: Optional[asyncio.Task] = None
        self._last_offset: int = 0

    async def start(self) -> None:
        """Start tailing the events JSONL file."""
        # Load existing events on startup
        self._load_all_events()
        self._tail_task = asyncio.create_task(self._tail_loop())

    async def stop(self) -> None:
        """Stop tailing."""
        if self._tail_task:
            self._tail_task.cancel()
            try:
                await self._tail_task
            except asyncio.CancelledError:
                pass

    def _load_all_events(self) -> None:
        """Load all existing events from JSONL on startup."""
        if not self._events_file.exists():
            return
        try:
            content = self._events_file.read_text()
            self._last_offset = len(content.encode())
            for line in content.strip().splitlines():
                try:
                    event = json.loads(line)
                    self._recent_events.append(event)
                    if len(self._recent_events) > self._max_recent:
                        self._recent_events = self._recent_events[-self._max_recent :]
                except json.JSONDecodeError:
                    continue
        except OSError as e:
            logger.warning(f"Failed to load events file: {e}")

    async def _tail_loop(self) -> None:
        """Tail events.jsonl using watchfiles for efficient file watching."""
        try:
            from watchfiles import awatch

            async for changes in awatch(self._events_file.parent):
                for change_type, path in changes:
                    if Path(path) == self._events_file:
                        self._load_new_events()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Event tail loop error: {e}")

    def _load_new_events(self) -> None:
        """Load new events since last read offset."""
        if not self._events_file.exists():
            return
        try:
            with open(self._events_file, "rb") as f:
                f.seek(self._last_offset)
                new_data = f.read()
                if not new_data:
                    return
                self._last_offset = f.tell()
                for line in new_data.decode().strip().splitlines():
                    try:
                        event = json.loads(line)
                        self._recent_events.append(event)
                        if len(self._recent_events) > self._max_recent:
                            self._recent_events = self._recent_events[-self._max_recent :]
                        # Fan out to subscribers
                        for queue in self._subscribers:
                            try:
                                queue.put_nowait(event)
                            except asyncio.QueueFull:
                                pass
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            logger.warning(f"Failed to read new events: {e}")

    def get_events_after_seq(self, seq: int) -> List[dict]:
        """Get events after a given global_seq for reconnection."""
        return [e for e in self._recent_events if e.get("global_seq", 0) > seq]

    def get_events_for_txn(self, txn_id: str) -> List[dict]:
        """Get all recent events for a specific transaction."""
        return [e for e in self._recent_events if e.get("txn_id") == txn_id]

    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to real-time events. Returns an async queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe a queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
