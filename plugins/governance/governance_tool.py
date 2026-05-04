"""governance_committee tool — entry point for the 三省六部 governance chain."""

import json
from dataclasses import asdict
from typing import Any, Dict

from .ministry_router import MinistryRouter
from .models import GovernanceResult
from .resident_manager import ResidentAgentManager
from .state_machine import GovernanceStateMachine

GOVERNANCE_COMMITTEE_SCHEMA = {
    "name": "governance_committee",
    "description": (
        "通过三省六部治理链执行任务。自动经过规划(中书省)→审核(门下省)→分派(尚书省)→执行(六部)→整合(尚书省)。"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "goal": {
                "type": "string",
                "description": "要完成的任务",
            },
            "context": {
                "type": "string",
                "description": "背景信息",
            },
            "priority": {
                "type": "string",
                "enum": ["low", "normal", "high", "critical"],
                "description": "优先级",
            },
            "skip_review": {
                "type": "boolean",
                "description": "跳过门下省审核（仅限低风险/内部策略/例行任务）",
            },
        },
        "required": ["goal"],
    },
}


def governance_committee_handler(args: Dict[str, Any], **kwargs) -> str:
    """
    Entry point. Creates transaction → advances state machine → returns result.
    All business logic lives in GovernanceStateMachine.
    """
    goal = args.get("goal", "")
    if not goal.strip():
        return json.dumps({"error": "goal is required"})

    context = args.get("context", "")
    priority = args.get("priority", "normal")
    skip_review = args.get("skip_review", False)
    parent_agent = kwargs.get("parent_agent")

    # Initialize components
    manager = ResidentAgentManager()
    manager.initialize()
    router = MinistryRouter()
    sm = GovernanceStateMachine(manager, router)

    # Create transaction
    txn = sm.create_transaction(goal, context, priority)

    # skip_review permission control: low-risk only
    can_skip = (
        skip_review
        and priority in ("low", "normal")
        and not _is_external_task(goal)
    )

    if can_skip:
        # PLAN only, skip REVIEW
        txn = sm.advance(txn, parent_agent)  # runs PLAN
        txn.state = "dispatch_complete"  # skip REVIEW
        txn.audit_trail.append({
            "step": "review", "action": "skipped",
            "reason": "low-risk skip_review",
        })
        manager.state_store.save_transaction(txn)
        txn = sm.advance(txn, parent_agent)  # DISPATCH → EXECUTE → INTEGRATE
    else:
        txn = sm.advance(txn, parent_agent)  # full chain

    # Build result
    result = GovernanceResult(
        status=txn.state,
        transaction_id=txn.transaction_id,
        integrated_result=txn.integrated_result,
        audit_trail=txn.audit_trail,
        error=(
            txn.audit_trail[-1].get("error")
            if txn.state == "error" and txn.audit_trail
            else None
        ),
    )
    return json.dumps(asdict(result), default=str, ensure_ascii=False)


def _is_external_task(goal: str) -> bool:
    """Check if task involves external operations (skip_review not allowed)."""
    external_keywords = [
        "deploy", "push", "publish", "send", "delete", "drop",
        "external", "api", "webhook",
    ]
    lower = goal.lower()
    return any(kw in lower for kw in external_keywords)
