"""Governance hook — intercepts delegate_task in strict mode."""

from typing import Any, Dict, Optional


def on_pre_tool_call(
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> Optional[Dict[str, Any]]:
    """
    Intercept delegate_task when governance is in strict mode.

    - off: no interception
    - soft: no interception, but audit log could be added later
    - strict: block delegate_task, redirect to governance_committee
    """
    if tool_name != "delegate_task":
        return None

    mode = _get_governance_mode()
    if mode == "off":
        return None

    if mode == "soft":
        # soft: delegate_task proceeds normally, governance is advisory
        return None

    # strict: block and redirect
    goal = (args or {}).get("goal", "")
    return {
        "action": "block",
        "message": (
            "治理模式 (strict) 已启用。请使用 governance_committee 工具代替 delegate_task。\n"
            "用法：governance_committee(goal='你的任务描述')\n"
            f"原任务：{goal[:200]}"
        ),
    }


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
