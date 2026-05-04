"""Governance chain state machine — core logic for 三省六部.

Each state transition is independent, testable, and recoverable.
Two usage modes:
  1. advance(txn) — auto-advance to terminal state (COMPLETE/REJECTED/ERROR)
  2. step_xxx(txn) — single-step for unit tests and fine control
"""

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from .ministry_router import MinistryRouter
from .models import (
    AgentRole,
    DelegationContract,
    GovernanceTransaction,
    TransactionState,
)
from .resident_manager import ResidentAgentManager
from .state_store import GovernanceStateStore


def _deadline(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


class GovernanceStateMachine:
    """Governance chain state machine. Each step independently testable."""

    MAX_RETRIES = 1
    ACCEPT_PARTIAL = True

    def __init__(self, manager: ResidentAgentManager, router: MinistryRouter):
        self._manager = manager
        self._router = router
        self._store: GovernanceStateStore = manager.state_store

    def create_transaction(
        self, goal: str, context: str, priority: str
    ) -> GovernanceTransaction:
        """Create a new transaction, persist to CREATED state."""
        txn = GovernanceTransaction(
            transaction_id=f"txn_{uuid4().hex[:12]}",
            goal=goal,
            context=context,
            priority=priority,
            state=TransactionState.CREATED.value,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._store.save_transaction(txn)
        return txn

    def advance(
        self, txn: GovernanceTransaction, parent_agent=None
    ) -> GovernanceTransaction:
        """
        Advance transaction to terminal state.
        Skips already-completed states (crash recovery).
        Persists after each step.
        """
        terminal = {
            TransactionState.COMPLETE.value,
            TransactionState.REJECTED.value,
            TransactionState.ERROR.value,
        }
        while txn.state not in terminal:
            handler = self._get_handler(txn.state)
            try:
                txn = handler(txn, parent_agent)
                self._store.save_transaction(txn)
            except Exception as e:
                txn.state = TransactionState.ERROR.value
                txn.audit_trail.append({"step": txn.state, "error": str(e)})
                self._store.save_transaction(txn)
                break
        return txn

    # --- Single-step interfaces (independently testable) ---

    def step_plan(self, txn, parent_agent=None):
        return self._step_plan(txn, parent_agent)

    def step_review(self, txn, parent_agent=None):
        return self._step_review(txn, parent_agent)

    def step_dispatch(self, txn, parent_agent=None):
        return self._step_dispatch(txn, parent_agent)

    def step_execute(self, txn, parent_agent=None):
        return self._step_execute(txn, parent_agent)

    def step_integrate(self, txn, parent_agent=None):
        return self._step_integrate(txn, parent_agent)

    # --- Handler dispatch ---

    def _get_handler(self, state: str):
        handlers = {
            TransactionState.CREATED.value: self._step_plan,
            TransactionState.PLAN_COMPLETE.value: self._step_review,
            TransactionState.REVIEW_COMPLETE.value: self._step_dispatch,
            TransactionState.DISPATCH_COMPLETE.value: self._step_execute,
            TransactionState.EXECUTE_COMPLETE.value: self._step_integrate,
        }
        return handlers.get(state, self._step_error)

    # --- Step implementations ---

    def _step_plan(self, txn, parent_agent) -> GovernanceTransaction:
        """中书省: planning."""
        txn.state = TransactionState.PLAN.value
        contract = DelegationContract(
            delegation_id=f"plan_{txn.transaction_id}",
            task=f"设计执行方案：{txn.goal}",
            success_criteria=["产出清晰的执行步骤和验证方法"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=5),
            result_format={"type": "json"},
            ministry="zhongshu",
            priority=txn.priority,
            notes=txn.context,
        )
        result = self._manager.activate_agent(AgentRole.ZHONGSHU, contract, parent_agent)
        txn.plan = result
        txn.state = TransactionState.PLAN_COMPLETE.value
        txn.audit_trail.append({"step": "zhongshu", "action": "plan_complete"})
        return txn

    def _step_review(self, txn, parent_agent) -> GovernanceTransaction:
        """门下省: review. Supports approve / reject / revise."""
        txn.state = TransactionState.REVIEW.value
        contract = DelegationContract(
            delegation_id=f"review_{txn.transaction_id}_r{txn.revision_count}",
            task="审核执行方案的完整性、可行性和风险",
            success_criteria=["给出明确的 approve/reject/revise 判定"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=3),
            result_format={"type": "json"},
            ministry="menxia",
            priority=txn.priority,
            notes=json.dumps({"plan": txn.plan, "original_goal": txn.goal}, ensure_ascii=False),
        )
        result = self._manager.activate_agent(AgentRole.MENGXIA, contract, parent_agent)

        # Parse verdict from result
        verdict = result.get("summary", "")
        parsed = self._parse_verdict(verdict)
        txn.review_verdict = parsed["verdict"]
        txn.review_notes = parsed.get("notes", "")

        if parsed["verdict"] == "reject":
            txn.state = TransactionState.REJECTED.value
            txn.audit_trail.append({
                "step": "menxia", "action": "rejected",
                "reason": txn.review_notes,
            })
        elif parsed["verdict"] == "revise" and txn.revision_count < 3:
            txn.revision_history.append({
                "round": txn.revision_count + 1,
                "reason": txn.review_notes,
                "plan_snapshot": txn.plan,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            txn.revision_count += 1
            txn.state = TransactionState.CREATED.value  # back to 中书省
            txn.audit_trail.append({
                "step": "menxia", "action": "revise",
                "round": txn.revision_count, "reason": txn.review_notes,
            })
        else:
            txn.state = TransactionState.REVIEW_COMPLETE.value
            txn.audit_trail.append({"step": "menxia", "action": "approved"})
        return txn

    def _step_dispatch(self, txn, parent_agent) -> GovernanceTransaction:
        """尚书省: split tasks into contracts."""
        txn.state = TransactionState.DISPATCH.value
        contracts = self._router.split_tasks(txn.goal, txn.context)
        txn.contracts = [asdict(c) for c in contracts]
        txn.state = TransactionState.DISPATCH_COMPLETE.value
        txn.audit_trail.append({
            "step": "shangshu", "action": f"dispatched {len(contracts)} task(s)",
        })
        return txn

    def _step_execute(self, txn, parent_agent) -> GovernanceTransaction:
        """六部: execute contracts with retry and partial-result acceptance."""
        txn.state = TransactionState.EXECUTE.value
        for contract_dict in txn.contracts:
            contract = DelegationContract(**contract_dict)
            role = contract.ministry

            if not self._store.acquire_task_lock(role, contract.delegation_id):
                txn.results.append({
                    "ministry": role, "status": "skipped",
                    "reason": "agent busy",
                })
                continue

            attempt = 0
            try:
                while attempt <= self.MAX_RETRIES:
                    try:
                        result = self._manager.activate_agent(
                            AgentRole(role), contract, parent_agent
                        )
                        txn.results.append({
                            "ministry": role, "status": "completed", "result": result,
                        })
                        break
                    except Exception as e:
                        attempt += 1
                        if attempt > self.MAX_RETRIES:
                            txn.results.append({
                                "ministry": role, "status": "failed",
                                "error": str(e), "attempts": attempt,
                            })
                        else:
                            txn.audit_trail.append({
                                "step": role, "action": "retry",
                                "attempt": attempt, "error": str(e),
                            })
            finally:
                self._store.release_task_lock(role, contract.delegation_id)

        failed = [r for r in txn.results if r["status"] == "failed"]
        completed = [r for r in txn.results if r["status"] == "completed"]

        if failed and not completed:
            txn.state = TransactionState.ERROR.value
            txn.audit_trail.append({
                "step": "execute", "action": "all_failed",
                "failed_count": len(failed),
            })
        elif failed and self.ACCEPT_PARTIAL:
            txn.state = TransactionState.EXECUTE_COMPLETE.value
            txn.audit_trail.append({
                "step": "execute", "action": "partial_success",
                "completed": len(completed), "failed": len(failed),
            })
        else:
            txn.state = TransactionState.EXECUTE_COMPLETE.value
            txn.audit_trail.append({
                "step": "execute", "action": "all_completed",
                "count": len(completed),
            })
        return txn

    def _step_integrate(self, txn, parent_agent) -> GovernanceTransaction:
        """尚书省: integrate results. Filters 兵部 boundary violations."""
        parts = []
        for r in txn.results:
            ministry = r.get("ministry", "?")
            status = r.get("status", "?")
            # 兵部 hard constraint: no final deliverables or state judgments
            if ministry == "bingbu" and self._violates_bingbu_boundary(r):
                txn.audit_trail.append({
                    "step": "integrate", "action": "boundary_violation",
                    "ministry": "bingbu",
                    "detail": "输出包含越界内容，已过滤",
                })
                continue
            summary = r.get("result", {}).get("summary", r.get("error", "no output"))
            parts.append(f"### {ministry} ({status})\n{summary}")

        txn.integrated_result = "\n\n".join(parts) if parts else "无结果"
        txn.state = TransactionState.COMPLETE.value
        txn.audit_trail.append({"step": "integrate", "action": "complete"})
        return txn

    def _violates_bingbu_boundary(self, result: dict) -> bool:
        """Check if 兵部 output contains state judgments or final deliverables."""
        summary = result.get("result", {}).get("summary", "")
        violation_markers = [
            "COMPLETE", "REJECTED", "APPROVED",
            "状态已更新", "任务完成", "最终结果",
        ]
        return any(marker in summary for marker in violation_markers)

    def _step_error(self, txn, parent_agent) -> GovernanceTransaction:
        txn.state = TransactionState.ERROR.value
        return txn

    @staticmethod
    def _parse_verdict(summary: str) -> Dict[str, Any]:
        """
        Parse 门下省 verdict from agent summary.
        Looks for JSON with verdict field, or keyword matching.
        """
        # Try JSON parse first
        try:
            # Look for JSON block in the summary
            if "{" in summary:
                start = summary.index("{")
                # Find matching closing brace
                depth = 0
                for i, ch in enumerate(summary[start:], start):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            data = json.loads(summary[start:i + 1])
                            if "verdict" in data:
                                return data
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: keyword matching
        lower = summary.lower()
        if "reject" in lower or "驳回" in lower or "拒绝" in lower:
            return {"verdict": "reject", "notes": summary[:300]}
        if "revise" in lower or "修改" in lower or "打回" in lower:
            return {"verdict": "revise", "notes": summary[:300]}
        return {"verdict": "approve", "notes": summary[:300]}
