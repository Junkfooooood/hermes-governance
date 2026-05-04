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
    GovernanceTransaction,
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
        self._agent_dir.mkdir(parents=True, exist_ok=True)
        self._txn_dir.mkdir(parents=True, exist_ok=True)

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
