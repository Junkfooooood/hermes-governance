"""Safe reader for governance state files with JSON parse error tolerance.

Maps governance plugin's `transaction_id` to dashboard's `txn_id` at read boundary.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GovernanceBridge:
    """Read-only bridge to governance state files."""

    def __init__(self, state_dir: Path):
        self._state_dir = state_dir
        self._txn_dir = state_dir / "transactions"
        self._agent_dir = state_dir / "agents"
        self._memory_dir = state_dir / "memory"
        self._feedback_path = state_dir / "rule_feedback.jsonl"

    # --- Helpers ---

    def _safe_read_json(self, path: Path) -> Optional[dict]:
        """Read JSON file with error tolerance. Returns None on failure."""
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, TypeError, OSError) as e:
            logger.warning(f"Failed to parse {path.name}: {e}")
            return None

    def _map_transaction(self, raw: dict) -> dict:
        """Map governance plugin field names to dashboard API field names."""
        mapped = dict(raw)
        if "transaction_id" in mapped:
            mapped["txn_id"] = mapped.pop("transaction_id")
        return mapped

    def _safe_read_jsonl(self, path: Path, limit: int = 200) -> List[dict]:
        """Read last N lines from a JSONL file with error tolerance."""
        if not path.exists():
            return []
        results: List[dict] = []
        try:
            lines = path.read_text().strip().splitlines()
            for line in lines[-limit:]:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except OSError as e:
            logger.warning(f"Failed to read {path.name}: {e}")
        return results

    def _append_jsonl(self, path: Path, record: dict) -> None:
        """Append a JSON record to a JSONL file."""
        try:
            with open(path, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"Failed to append to {path.name}: {e}")

    def _read_alert_state(self) -> Dict[str, dict]:
        """Read alert processing state."""
        data = self._safe_read_json(self._state_dir / "alert_state.json")
        return data if isinstance(data, dict) else {}

    def _write_alert_state(self, state: Dict[str, dict]) -> None:
        """Write alert processing state atomically."""
        path = self._state_dir / "alert_state.json"
        tmp = path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            tmp.replace(path)
        except OSError as e:
            logger.warning(f"Failed to write alert_state.json: {e}")

    # --- Transactions ---

    def load_transaction(self, txn_id: str) -> Optional[dict]:
        """Load single transaction by txn_id."""
        # Try direct file lookup
        path = self._txn_dir / f"{txn_id}.json"
        raw = self._safe_read_json(path)
        if raw:
            return self._map_transaction(raw)
        # Fallback: scan all files (for cases where filename differs)
        if self._txn_dir.exists():
            for f in self._txn_dir.glob("*.json"):
                raw = self._safe_read_json(f)
                if raw and raw.get("transaction_id") == txn_id:
                    return self._map_transaction(raw)
        return None

    def load_all_transactions(self) -> List[dict]:
        """Load all transaction files with error tolerance."""
        if not self._txn_dir.exists():
            return []
        results = []
        for f in self._txn_dir.glob("*.json"):
            raw = self._safe_read_json(f)
            if raw:
                results.append(self._map_transaction(raw))
        return results

    # --- Agents ---

    def load_agent_state(self, role: str) -> Optional[dict]:
        """Load agent state from agents/{role}.json."""
        path = self._agent_dir / f"{role}.json"
        return self._safe_read_json(path)

    def load_all_agents(self) -> List[dict]:
        """Load all agent state files."""
        if not self._agent_dir.exists():
            return []
        results = []
        for f in self._agent_dir.glob("*.json"):
            raw = self._safe_read_json(f)
            if raw:
                results.append(raw)
        return results

    # --- Memory ---

    def load_boulder_state(self) -> Optional[dict]:
        return self._safe_read_json(self._memory_dir / "boulder_state.json")

    def load_decision_log(self) -> Optional[dict]:
        return self._safe_read_json(self._memory_dir / "decision_log.json")

    def load_notepad_wisdom(self) -> Optional[dict]:
        return self._safe_read_json(self._memory_dir / "notepad_wisdom.json")

    # --- Feedback ---

    def load_rule_feedback(self, limit: int = 200) -> List[dict]:
        return self._safe_read_jsonl(self._feedback_path, limit)

    # --- Annotations (Dashboard-owned) ---

    def load_annotations(
        self, txn_id: Optional[str] = None, include_deleted: bool = False
    ) -> List[dict]:
        path = self._state_dir / "annotations.jsonl"
        all_anns = self._safe_read_jsonl(path, limit=10000)
        if not include_deleted:
            all_anns = [a for a in all_anns if not a.get("deleted")]
        if txn_id:
            all_anns = [a for a in all_anns if a.get("txn_id") == txn_id]
        return all_anns

    def save_annotation(self, annotation: dict) -> None:
        self._append_jsonl(self._state_dir / "annotations.jsonl", annotation)

    def update_annotation(self, annotation_id: str, updates: dict) -> bool:
        """Update an annotation by ID. Returns True if found."""
        path = self._state_dir / "annotations.jsonl"
        anns = self._safe_read_jsonl(path, limit=10000)
        found = False
        for ann in anns:
            if ann.get("annotation_id") == annotation_id:
                ann.update(updates)
                found = True
                break
        if found:
            # Rewrite file
            tmp = path.with_suffix(".tmp")
            try:
                tmp.write_text(
                    "\n".join(json.dumps(a, ensure_ascii=False) for a in anns) + "\n"
                )
                tmp.replace(path)
            except OSError as e:
                logger.warning(f"Failed to rewrite annotations: {e}")
                return False
        return found

    # --- Alert state (Dashboard-owned) ---

    def get_alert_state(self, alert_id: str) -> Optional[dict]:
        state = self._read_alert_state()
        return state.get(alert_id)

    def save_alert_state(self, alert_id: str, alert_state: dict) -> None:
        state = self._read_alert_state()
        state[alert_id] = alert_state
        self._write_alert_state(state)
