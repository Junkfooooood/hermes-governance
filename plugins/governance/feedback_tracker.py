"""Feedback tracker — Entropy Management for governance rules.

Records rule violations, compliance, positive feedback, ignored rules,
and confusing rules. Provides drift reports with root cause analysis.

All entries are append-only JSONL for auditability.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class FeedbackTracker:
    """Tracks governance rule effectiveness and drift.

    Feedback types:
    - violation: agent broke a rule
    - compliance: agent followed all rules
    - helpful_rule: rule helped complete the task (positive signal)
    - ignored_rule: agent didn't follow rule but no hard violation
    - confusing_rule: rule wording unclear, agent struggled
    """

    def __init__(self, state_dir: Path):
        self._log_path = Path(state_dir) / "rule_feedback.jsonl"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Recording methods ---

    def record_violation(
        self, transaction_id: str, role: str, rule_id: str, detail: str
    ) -> None:
        """Record a rule violation event."""
        self._append({
            "type": "violation",
            "transaction_id": transaction_id,
            "role": role,
            "rule_id": rule_id,
            "detail": detail[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_compliance(
        self, transaction_id: str, role: str,
        rules_checked: int, rules_passed: int,
    ) -> None:
        """Record a compliance event (all rules passed)."""
        self._append({
            "type": "compliance",
            "transaction_id": transaction_id,
            "role": role,
            "checked": rules_checked,
            "passed": rules_passed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_helpful(
        self, transaction_id: str, role: str, rule_id: str
    ) -> None:
        """Record positive feedback: rule was helpful for task completion."""
        self._append({
            "type": "helpful_rule",
            "transaction_id": transaction_id,
            "role": role,
            "rule_id": rule_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_ignored(
        self, transaction_id: str, role: str, rule_id: str, context: str
    ) -> None:
        """Record an ignored rule (not a hard violation, but not followed)."""
        self._append({
            "type": "ignored_rule",
            "transaction_id": transaction_id,
            "role": role,
            "rule_id": rule_id,
            "context": context[:300],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def record_confusing(
        self, transaction_id: str, role: str, rule_id: str, detail: str
    ) -> None:
        """Record a confusing rule (wording unclear, agent struggled)."""
        self._append({
            "type": "confusing_rule",
            "transaction_id": transaction_id,
            "role": role,
            "rule_id": rule_id,
            "detail": detail[:300],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # --- Query methods ---

    def get_rule_effectiveness(self, rule_id: str) -> Dict[str, Any]:
        """Get effectiveness stats for a specific rule.

        Returns:
            {
                "rule_id": "...",
                "violation_count": N,
                "helpful_count": N,
                "ignored_count": N,
                "confusing_count": N,
                "compliance_rate": 0.0-1.0,
            }
        """
        entries = self._load_entries()
        violations = [e for e in entries if e.get("rule_id") == rule_id and e["type"] == "violation"]
        helpful = [e for e in entries if e.get("rule_id") == rule_id and e["type"] == "helpful_rule"]
        ignored = [e for e in entries if e.get("rule_id") == rule_id and e["type"] == "ignored_rule"]
        confusing = [e for e in entries if e.get("rule_id") == rule_id and e["type"] == "confusing_rule"]

        total = len(violations) + len(helpful) + len(ignored)
        compliance_rate = len(helpful) / total if total > 0 else 1.0

        return {
            "rule_id": rule_id,
            "violation_count": len(violations),
            "helpful_count": len(helpful),
            "ignored_count": len(ignored),
            "confusing_count": len(confusing),
            "compliance_rate": round(compliance_rate, 3),
        }

    def get_drift_report(self) -> Dict[str, Any]:
        """Generate a drift report with root cause analysis.

        Returns:
            {
                "total_events": N,
                "top_violated_rules": [{"rule_id": ..., "count": N, "roles": [...]}],
                "top_ignored_rules": [{"rule_id": ..., "count": N}],
                "top_confusing_rules": [{"rule_id": ..., "count": N}],
                "role_violation_ranking": [{"role": ..., "count": N}],
                "root_cause_hints": [{"rule_id": ..., "hint": "..."}],
            }
        """
        entries = self._load_entries()

        if not entries:
            return {"total_events": 0, "top_violated_rules": [], "top_ignored_rules": [],
                    "top_confusing_rules": [], "role_violation_ranking": [], "root_cause_hints": []}

        # Count violations by rule
        violation_by_rule: Dict[str, List[str]] = defaultdict(list)
        ignored_by_rule: Counter = Counter()
        confusing_by_rule: Counter = Counter()
        violations_by_role: Counter = Counter()

        for e in entries:
            if e["type"] == "violation":
                rule_id = e.get("rule_id", "unknown")
                role = e.get("role", "unknown")
                violation_by_rule[rule_id].append(role)
                violations_by_role[role] += 1
            elif e["type"] == "ignored_rule":
                ignored_by_rule[e.get("rule_id", "unknown")] += 1
            elif e["type"] == "confusing_rule":
                confusing_by_rule[e.get("rule_id", "unknown")] += 1

        # Top violated rules
        top_violated = [
            {"rule_id": rid, "count": len(roles), "roles": list(set(roles))}
            for rid, roles in sorted(violation_by_rule.items(), key=lambda x: -len(x[1]))[:10]
        ]

        # Top ignored rules
        top_ignored = [
            {"rule_id": rid, "count": count}
            for rid, count in ignored_by_rule.most_common(10)
        ]

        # Top confusing rules
        top_confusing = [
            {"rule_id": rid, "count": count}
            for rid, count in confusing_by_rule.most_common(10)
        ]

        # Role violation ranking
        role_ranking = [
            {"role": role, "count": count}
            for role, count in violations_by_role.most_common()
        ]

        # Root cause analysis
        root_causes = self._analyze_root_causes(
            violation_by_rule, ignored_by_rule, confusing_by_rule
        )

        return {
            "total_events": len(entries),
            "top_violated_rules": top_violated,
            "top_ignored_rules": top_ignored,
            "top_confusing_rules": top_confusing,
            "role_violation_ranking": role_ranking,
            "root_cause_hints": root_causes,
        }

    def _analyze_root_causes(
        self,
        violation_by_rule: Dict[str, List[str]],
        ignored_by_rule: Counter,
        confusing_by_rule: Counter,
    ) -> List[Dict[str, str]]:
        """Analyze root causes for frequently violated/ignored/confusing rules."""
        hints = []

        for rule_id, roles in violation_by_rule.items():
            if len(roles) < 2:
                continue

            unique_roles = set(roles)
            # Check if only one role violates (might be role-specific issue)
            if len(unique_roles) == 1:
                hints.append({
                    "rule_id": rule_id,
                    "hint": f"Only {list(unique_roles)[0]} violates this rule — "
                            f"may not be applicable to this role",
                })
            # Check if all roles violate (rule might be unclear or too strict)
            elif len(unique_roles) >= 3:
                hint = f"Violated by {len(unique_roles)} different roles"
                if confusing_by_rule.get(rule_id, 0) > 0:
                    hint += " + reported as confusing — rule wording may need clarification"
                else:
                    hint += " — rule may be too strict or poorly positioned in prompt"
                hints.append({"rule_id": rule_id, "hint": hint})

        # Rules that are both ignored and confusing
        for rule_id in ignored_by_rule:
            if confusing_by_rule.get(rule_id, 0) > 0:
                hints.append({
                    "rule_id": rule_id,
                    "hint": "Both ignored and confusing — rewrite rule for clarity",
                })

        return hints

    # --- Internal methods ---

    def _append(self, entry: Dict[str, Any]) -> None:
        """Append an entry to the JSONL log file (atomic)."""
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def _load_entries(self) -> List[Dict[str, Any]]:
        """Load all feedback entries from the JSONL log."""
        if not self._log_path.exists():
            return []
        entries = []
        for line in self._log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries
