"""Governance hook — intercepts delegate_task with hard gate enforcement."""

from typing import Any, Dict, Optional

# Hard gate keywords: these tasks MUST go through governance chain
_HARD_GATE_CATEGORIES = {
    "external": ["deploy", "push", "publish", "send", "delete", "drop",
                 "发布", "部署", "删除", "推送", "发送"],
    "security": ["auth", "permission", "credential", "secret", "token", "password",
                 "认证", "权限", "密钥", "密码", "凭证"],
    "architecture": ["refactor", "migrate", "schema", "database",
                     "架构", "重构", "迁移", "数据库"],
}


def on_pre_tool_call(
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> Optional[Dict[str, Any]]:
    """
    Intercept delegate_task:
    - off: no interception
    - soft: hard gate only (block dangerous tasks, let others pass)
    - strict: block all delegate_task, redirect to governance_committee
    """
    if tool_name != "delegate_task":
        return None

    mode = _get_governance_mode()
    if mode == "off":
        return None

    goal = (args or {}).get("goal", "")

    # Hard gate: always block dangerous tasks regardless of mode
    blocked, reason = _check_hard_gate(goal)
    if blocked:
        return {
            "action": "block",
            "message": (
                f"[硬门控] {reason}\n"
                "请使用 governance_committee 工具：\n"
                f"governance_committee(goal='{goal[:200]}')"
            ),
        }

    if mode == "soft":
        # soft: non-dangerous tasks pass through
        return None

    # strict: block all delegate_task
    return {
        "action": "block",
        "message": (
            "治理模式 (strict) 已启用。请使用 governance_committee 工具代替 delegate_task。\n"
            "用法：governance_committee(goal='你的任务描述')\n"
            f"原任务：{goal[:200]}"
        ),
    }


def _check_hard_gate(goal: str) -> tuple:
    """Check if goal triggers hard gate. Returns (blocked, reason)."""
    lower = goal.lower()
    for category, keywords in _HARD_GATE_CATEGORIES.items():
        matches = [kw for kw in keywords if kw in lower]
        if matches:
            return True, (
                f"此任务触及 {category} 类关键词 ({', '.join(matches[:3])})，"
                f"必须通过治理链执行。"
            )
    return False, ""


def on_session_end(
    session_id: str = "",
    transcript: str = "",
    **_: Any,
) -> None:
    """
    Session reset 时自动将关键对话摘要写入记忆库。
    类似 OMC 的 session-memory 持久化。
    """
    if not transcript or len(transcript) < 200:
        return  # 太短的对话不需要摘要

    try:
        from .state_store import GovernanceStateStore
        store = GovernanceStateStore()

        # 提取对话摘要（取最后 2000 字符作为关键内容）
        tail = transcript[-2000:] if len(transcript) > 2000 else transcript

        # 记录到 notepad wisdom
        store.add_wisdom(
            pattern=f"Session {session_id[:16]}... ended",
            context=tail[:500],
            discovered_by="session_auto_summary",
        )
    except Exception:
        pass  # 静默失败，不影响 session 关闭


def _get_governance_mode() -> str:
    """Read governance mode from config: strict / soft / off."""
    try:
        import sys
        from pathlib import Path

        hermes_agent_dir = str(Path.home() / ".hermes" / "hermes-agent")
        if hermes_agent_dir not in sys.path:
            sys.path.insert(0, hermes_agent_dir)

        from hermes_cli.config import load_config
        config = load_config()
        gov = config.get("governance", {})
        if not gov.get("enabled", False):
            return "off"
        return gov.get("mode", "strict")
    except Exception:
        return "off"
