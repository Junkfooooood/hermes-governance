"""Persistent state storage with version control and task-level locks."""

import json
import os
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    AgentLifecycle,
    AgentRole,
    BoulderState,
    DecisionLog,
    GovernanceTransaction,
    NotepadWisdom,
    ResidentAgentState,
    TransactionState,
)


class GovernanceStateStore:
    """Persistent state storage with optimistic versioning and task-level locks."""

    def __init__(self, state_dir: Optional[Path] = None):
        self._state_dir = state_dir or (Path.home() / ".hermes" / "governance" / "state")
        self._agent_dir = self._state_dir / "agents"
        self._txn_dir = self._state_dir / "transactions"
        self._lock = threading.Lock()
        self._active_locks: Dict[str, str] = {}  # role -> contract_id

        # Ensure directories exist
        self._memory_dir = self._state_dir / "memory"
        self._agent_dir.mkdir(parents=True, exist_ok=True)
        self._txn_dir.mkdir(parents=True, exist_ok=True)
        self._memory_dir.mkdir(parents=True, exist_ok=True)

    # --- Agent State ---

    def load_agent_state(self, role: str) -> ResidentAgentState:
        """Load agent state from disk. Returns default state if not found."""
        path = self._agent_dir / f"{role}.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return ResidentAgentState(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        # Default state
        tier = "ministry" if role in ("zhongshu", "menxia", "shangshu") else "department"
        return ResidentAgentState(
            agent_id=f"agent_{role}",
            role=role,
            tier=tier,
        )

    def save_agent_state(self, state: ResidentAgentState) -> bool:
        """
        Save agent state with optimistic lock check.
        Returns False if disk version > current version (conflict).
        """
        with self._lock:
            current = self._load_agent_from_disk(state.role)
            if current and current.version > state.version:
                return False  # version conflict
            state.version += 1
            state.updated_at = datetime.now(timezone.utc).isoformat()
            self._write_agent_to_disk(state)
            return True

    def _load_agent_from_disk(self, role: str) -> Optional[ResidentAgentState]:
        path = self._agent_dir / f"{role}.json"
        if path.exists():
            try:
                return ResidentAgentState(**json.loads(path.read_text()))
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    def _write_agent_to_disk(self, state: ResidentAgentState) -> None:
        path = self._agent_dir / f"{state.role}.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False, default=str))
        os.replace(str(tmp_path), str(path))

    # --- Task Locks ---

    def acquire_task_lock(self, role: str, contract_id: str) -> bool:
        """
        Try to acquire task lock. Same role cannot process multiple contracts.
        Returns True if acquired, False if role is busy.
        """
        with self._lock:
            if role in self._active_locks:
                return False
            self._active_locks[role] = contract_id
            return True

    def release_task_lock(self, role: str, contract_id: str) -> None:
        """Release task lock. Only the lock holder can release."""
        with self._lock:
            if self._active_locks.get(role) == contract_id:
                del self._active_locks[role]

    # --- Transaction Persistence (crash recovery) ---

    def save_transaction(self, txn: GovernanceTransaction) -> None:
        """Persist transaction state to disk (atomic write)."""
        txn.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._txn_dir / f"{txn.transaction_id}.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(asdict(txn), indent=2, ensure_ascii=False, default=str))
        os.replace(str(tmp_path), str(path))

    def load_transaction(self, txn_id: str) -> Optional[GovernanceTransaction]:
        """Load transaction from disk for crash recovery."""
        path = self._txn_dir / f"{txn_id}.json"
        if path.exists():
            try:
                return GovernanceTransaction(**json.loads(path.read_text()))
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    def get_pending_transactions(self) -> List[GovernanceTransaction]:
        """Find all incomplete transactions (for crash recovery)."""
        terminal_states = {
            TransactionState.COMPLETE.value,
            TransactionState.REJECTED.value,
            TransactionState.ERROR.value,
        }
        pending = []
        for path in self._txn_dir.glob("txn_*.json"):
            try:
                txn = GovernanceTransaction(**json.loads(path.read_text()))
                if txn.state not in terminal_states:
                    pending.append(txn)
            except (json.JSONDecodeError, TypeError):
                continue
        return pending

    # --- Structured Memory (Boulder State, Decision Log, Notepad Wisdom) ---

    def load_boulder_state(self) -> BoulderState:
        """Load project state tracker."""
        path = self._memory_dir / "boulder_state.json"
        if path.exists():
            try:
                return BoulderState(**json.loads(path.read_text()))
            except (json.JSONDecodeError, TypeError):
                pass
        return BoulderState()

    def save_boulder_state(self, state: BoulderState) -> None:
        """Save project state tracker."""
        state.last_updated = datetime.now(timezone.utc).isoformat()
        path = self._memory_dir / "boulder_state.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False, default=str))
        os.replace(str(tmp_path), str(path))

    def load_decision_log(self) -> DecisionLog:
        """Load decision log."""
        path = self._memory_dir / "decision_log.json"
        if path.exists():
            try:
                return DecisionLog(**json.loads(path.read_text()))
            except (json.JSONDecodeError, TypeError):
                pass
        return DecisionLog()

    def save_decision_log(self, log: DecisionLog) -> None:
        """Save decision log."""
        path = self._memory_dir / "decision_log.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(asdict(log), indent=2, ensure_ascii=False, default=str))
        os.replace(str(tmp_path), str(path))

    def append_decision(self, txn: GovernanceTransaction) -> None:
        """Append a completed transaction to the decision log."""
        log = self.load_decision_log()
        log.entries.append({
            "txn_id": txn.transaction_id,
            "goal": txn.goal[:200],
            "verdict": txn.review_verdict,
            "plan_summary": str(txn.plan)[:300] if txn.plan else None,
            "sub_task_count": len(txn.sub_tasks),
            "result_count": len(txn.results),
            "verify_passed": txn.verify_result.get("passed") if txn.verify_result else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Keep last 100 entries
        if len(log.entries) > 100:
            log.entries = log.entries[-100:]
        self.save_decision_log(log)

    def load_notepad_wisdom(self) -> NotepadWisdom:
        """Load notepad wisdom (patterns, pitfalls, best practices)."""
        path = self._memory_dir / "notepad_wisdom.json"
        if path.exists():
            try:
                return NotepadWisdom(**json.loads(path.read_text()))
            except (json.JSONDecodeError, TypeError):
                pass
        return NotepadWisdom()

    def save_notepad_wisdom(self, wisdom: NotepadWisdom) -> None:
        """Save notepad wisdom."""
        path = self._memory_dir / "notepad_wisdom.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(asdict(wisdom), indent=2, ensure_ascii=False, default=str))
        os.replace(str(tmp_path), str(path))

    def add_wisdom(self, pattern: str, context: str, discovered_by: str) -> None:
        """Add a new wisdom entry."""
        wisdom = self.load_notepad_wisdom()
        wisdom.patterns.append({
            "pattern": pattern,
            "context": context,
            "discovered_by": discovered_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(wisdom.patterns) > 200:
            wisdom.patterns = wisdom.patterns[-200:]
        self.save_notepad_wisdom(wisdom)
