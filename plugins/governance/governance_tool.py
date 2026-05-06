"""governance_committee tool — entry point for the 三省六部 governance chain."""

import json
from dataclasses import asdict
from typing import Any, Dict

from .ministry_router import MinistryRouter
from .models import GovernanceResult, TransactionState
from .resident_manager import ResidentAgentManager
from .state_machine import GovernanceStateMachine
from .event_bus import get_bus

GOVERNANCE_COMMITTEE_SCHEMA = {
    "name": "governance_committee",
    "description": (
        "通过三省六部治理链执行任务。"
        "自动经过澄清(中书省)→规划(中书省)→合规审核(门下省)→质量审核(门下省)"
        "→分解(尚书省)→分派(尚书省)→执行(六部)→验证(刑部)→整合(尚书省)。"
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
            "skip_interview": {
                "type": "boolean",
                "description": "跳过 Deep Interview（需求已明确时）",
            },
        },
        "required": ["goal"],
    },
}


# ============================================================
# Hard Gate: 强制使用治理链的场景
# ============================================================

HARD_GATE_KEYWORDS = {
    # 涉及外部操作必须走治理链
    "external": ["deploy", "push", "publish", "send", "delete", "drop",
                 "deploy", "发布", "部署", "删除", "推送", "发送"],
    # 涉及安全敏感操作
    "security": ["auth", "permission", "credential", "secret", "token", "password",
                 "认证", "权限", "密钥", "密码", "凭证"],
    # 涉及架构变更
    "architecture": ["refactor", "migrate", "schema", "database", "架构", "重构",
                     "迁移", "数据库"],
}


def _check_hard_gate(goal: str) -> tuple:
    """
    Check if goal triggers hard gate (must use governance chain).
    Returns (blocked: bool, reason: str).
    """
    lower = goal.lower()
    for category, keywords in HARD_GATE_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in lower]
        if matches:
            return True, (
                f"此任务触及 {category} 类关键词 ({', '.join(matches[:3])})，"
                f"必须通过治理链执行。请使用 governance_committee。"
            )
    return False, ""


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
    skip_interview = args.get("skip_interview", False)
    parent_agent = kwargs.get("parent_agent")

    # Load config
    config = _load_governance_config()

    # Initialize components
    manager = ResidentAgentManager(config=config)
    manager.initialize()
    router = MinistryRouter()

    # Wire event bus for dashboard real-time monitoring
    bus = get_bus()
    sm = GovernanceStateMachine(manager, router, event_callback=bus.emit)

    # Create transaction
    txn = sm.create_transaction(goal, context, priority)

    # Determine which stages to skip
    can_skip_review = (
        skip_review
        and priority in ("low", "normal")
        and not _is_external_task(goal)
    )
    can_skip_interview = skip_interview or priority == "low"

    # Execute governance chain
    if can_skip_review:
        # Skip review: INTERVIEW → PLAN → DECOMPOSE → DISPATCH → EXECUTE → VERIFY → INTEGRATE
        txn = sm.advance(txn, parent_agent)  # INTERVIEW → PLAN
        if can_skip_interview:
            txn.state = TransactionState.PLAN_COMPLETE.value  # skip interview
        txn = sm.advance(txn, parent_agent)  # through VERIFY → INTEGRATE
    else:
        # Full chain
        if can_skip_interview:
            # Skip interview only: go straight to PLAN
            txn.state = TransactionState.INTERVIEW_COMPLETE.value
            manager.state_store.save_transaction(txn)
        txn = sm.advance(txn, parent_agent)

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
    """Check if task involves external operations."""
    external_keywords = [
        "deploy", "push", "publish", "send", "delete", "drop",
        "external", "api", "webhook", "部署", "发布", "删除",
    ]
    lower = goal.lower()
    return any(kw in lower for kw in external_keywords)


def _load_governance_config() -> dict:
    """Load governance config from config.yaml."""
    try:
        import sys
        from pathlib import Path
        hermes_dir = str(Path.home() / ".hermes" / "hermes-agent")
        if hermes_dir not in sys.path:
            sys.path.insert(0, hermes_dir)
        from hermes_cli.config import load_config
        return load_config()
    except Exception:
        return {}
