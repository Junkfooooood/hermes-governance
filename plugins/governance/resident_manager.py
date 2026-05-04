"""Resident Agent Manager — manages agent lifecycle for 三省六部.

"Resident" means: persistent identity, memory, permissions on disk.
NOT: permanently-running Python objects or background workers.

Agents are activated on-demand: load state → create AIAgent → execute → persist state → release.
"""

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    AgentLifecycle,
    AgentRole,
    DelegationContract,
    ResidentAgentState,
)
from .state_store import GovernanceStateStore

# Role → harness role file mapping
_ROLE_FILE_MAP = {
    AgentRole.ZHONGSHU: "zhongshu.md",
    AgentRole.MENGXIA: "menxia.md",
    AgentRole.SHANGSHU: "shangshu.md",
    AgentRole.GONGBU: "gongbu.md",
    AgentRole.HUBU: "hubu.md",
    AgentRole.LIBU: "libu.md",
    AgentRole.BINGBU: "bingbu.md",
    AgentRole.XINGBU: "xingbu.md",
    AgentRole.LIBU_RENSHI: "libu-renshi.md",
}

# 三省 = planning (high reasoning), 六部 = execution (fast)
_PLANNING_ROLES = {AgentRole.ZHONGSHU, AgentRole.MENGXIA, AgentRole.SHANGSHU}
_EXECUTION_ROLES = {
    AgentRole.GONGBU, AgentRole.HUBU, AgentRole.LIBU,
    AgentRole.BINGBU, AgentRole.XINGBU, AgentRole.LIBU_RENSHI,
}


class ResidentAgentManager:
    """Manages resident agent lifecycle: load → activate → execute → persist → release."""

    def __init__(
        self,
        harness_dir: Optional[Path] = None,
        state_dir: Optional[Path] = None,
        config: Optional[dict] = None,
    ):
        self._harness_dir = harness_dir or Path.home() / ".hermes" / "harness"
        self._state_store = GovernanceStateStore(state_dir)
        self._config = config or {}
        self._role_prompts: Dict[str, str] = {}
        self._planning_models: List[dict] = []
        self._execution_models: List[dict] = []
        self._cursor_proxy_config: Optional[dict] = None

    @property
    def state_store(self) -> GovernanceStateStore:
        return self._state_store

    def initialize(self) -> None:
        """Load role definitions and model configs."""
        # Load role prompts
        roles_dir = self._harness_dir / "roles"
        for role, filename in _ROLE_FILE_MAP.items():
            path = roles_dir / filename
            if path.exists():
                self._role_prompts[role.value] = path.read_text()
            else:
                self._role_prompts[role.value] = f"You are {role.value}. Perform your assigned duties."

        # Load model configs
        gov_cfg = self._config.get("governance", {})
        self._planning_models = gov_cfg.get("planning_models", [])
        self._execution_models = gov_cfg.get("execution_models", [])

        # Cursor proxy
        from .cursor_proxy import get_cursor_proxy_config
        self._cursor_proxy_config = get_cursor_proxy_config(gov_cfg)

    def activate_agent(
        self,
        role: AgentRole,
        contract: DelegationContract,
        parent_agent=None,
    ) -> Dict[str, Any]:
        """Activate a resident agent to execute a contract."""
        state = self._load_and_activate(role)
        system_prompt = self._build_system_prompt(role, state, contract)
        toolsets = self._get_toolsets_for_role(role)

        state.lifecycle = AgentLifecycle.EXECUTE.value
        try:
            summary, tokens = self._run_agent(role, contract, system_prompt, toolsets, parent_agent)
        except Exception as e:
            state.lifecycle = AgentLifecycle.DEACTIVATE.value
            self._record_failure(state, contract, str(e))
            raise

        self._record_and_persist(state, contract, summary, tokens)
        return {"summary": summary, "tokens": tokens, "role": role.value}

    def _load_and_activate(self, role: AgentRole) -> ResidentAgentState:
        state = self._state_store.load_agent_state(role.value)
        state.lifecycle = AgentLifecycle.ACTIVATED.value
        state.last_activated = datetime.now(timezone.utc).isoformat()
        return state

    def _build_system_prompt(
        self,
        role: AgentRole,
        state: ResidentAgentState,
        contract: DelegationContract,
    ) -> str:
        """Build system prompt: role definition + structured memory + contract."""
        parts = []

        # 1. Role definition from harness
        role_prompt = self._role_prompts.get(role.value, "")
        if role_prompt:
            parts.append(role_prompt)

        # 2. Structured memory injection
        memory_sections = self._build_memory_sections(role)
        if memory_sections:
            parts.append(memory_sections)

        # 3. Accumulated agent memory (last 5 entries)
        if state.memory:
            recent = state.memory[-5:]
            memory_text = "\n".join(
                f"- [{m.get('timestamp', '?')[:10]}] {m.get('summary', '')}"
                for m in recent
            )
            parts.append(f"\n## Your Recent Memory\n{memory_text}")

        # 4. Contract details
        parts.append(f"\n## Current Task\n{contract.task}")
        if contract.success_criteria:
            criteria = "\n".join(f"- {c}" for c in contract.success_criteria)
            parts.append(f"\n## Success Criteria\n{criteria}")
        if contract.notes:
            parts.append(f"\n## Additional Context\n{contract.notes}")

        # 5. Bingbu hard constraint
        if role == AgentRole.BINGBU:
            parts.append(
                "\n## Hard Constraints (兵部)\n"
                "- You may ONLY produce execution process, NOT final deliverables.\n"
                "- You may ONLY modify execution path, NOT governance state.\n"
                "- Any result aggregation, state transition, or completion judgment "
                "MUST be handled by 尚书省 or 吏部."
            )

        # 6. Xingbu verification instructions
        if role == AgentRole.XINGBU:
            parts.append(
                "\n## Verification Protocol (刑部)\n"
                "- Execute success criteria checks from the contract.\n"
                "- Run tests, security scans, or validation as specified.\n"
                "- Output JSON: {\"passed\": true/false, \"checks\": [...], \"issues\": [...]}\n"
                "- Be strict: partial pass = fail."
            )

        return "\n".join(parts)

    def _build_memory_sections(self, role: AgentRole) -> str:
        """Build structured memory sections for system prompt."""
        parts = []

        # Boulder State (project status)
        boulder = self._state_store.load_boulder_state()
        if boulder.active_goals or boulder.blocked_goals:
            parts.append("\n## Project Status (Boulder State)")
            if boulder.active_goals:
                active = "\n".join(f"- {g.get('goal', '?')}" for g in boulder.active_goals[-5:])
                parts.append(f"**Active:**\n{active}")
            if boulder.blocked_goals:
                blocked = "\n".join(f"- {g.get('goal', '?')} (blocked: {g.get('reason', '?')})" for g in boulder.blocked_goals[-3:])
                parts.append(f"**Blocked:**\n{blocked}")

        # Decision Log (recent decisions)
        decisions = self._state_store.load_decision_log()
        if decisions.entries:
            recent = decisions.entries[-3:]
            decision_text = "\n".join(
                f"- [{d.get('timestamp', '?')[:10]}] {d.get('goal', '?')[:80]} → {d.get('verdict', '?')}"
                for d in recent
            )
            parts.append(f"\n## Recent Decisions\n{decision_text}")

        # Notepad Wisdom (patterns and pitfalls)
        wisdom = self._state_store.load_notepad_wisdom()
        if wisdom.patterns:
            recent = wisdom.patterns[-5:]
            wisdom_text = "\n".join(
                f"- **{p.get('pattern', '?')}** (context: {p.get('context', '?')[:60]})"
                for p in recent
            )
            parts.append(f"\n## Known Patterns & Pitfalls\n{wisdom_text}")

        return "\n".join(parts)

    def _get_model_for_role(self, role: AgentRole, parent_agent=None) -> str:
        """
        Get model string for a role.
        三省 → planning models (deepseek-v4-pro, mimo-2.5-pro, opus via cursor)
        六部 → execution models (minimax-m2.7, deepseek-v4-flash)
        """
        if role in _PLANNING_ROLES:
            # Try Cursor proxy first for Opus
            if self._cursor_proxy_config and role == AgentRole.ZHONGSHU:
                return self._cursor_proxy_config.get("model", "")

            # Use first available planning model
            for model_cfg in self._planning_models:
                provider = model_cfg.get("provider", "")
                model = model_cfg.get("model", "")
                if provider == "cursor" and self._cursor_proxy_config:
                    return self._cursor_proxy_config.get("model", "")
                if model:
                    return model

            # Default planning model
            default = self._config.get("governance", {}).get("default_planning_model", {})
            return default.get("model", "")

        elif role in _EXECUTION_ROLES:
            # Use first available execution model
            for model_cfg in self._execution_models:
                model = model_cfg.get("model", "")
                if model:
                    return model

            # Default execution model
            default = self._config.get("governance", {}).get("default_execution_model", {})
            return default.get("model", "")

        return ""

    def _get_agent_kwargs(self, role: AgentRole, parent_agent=None) -> dict:
        """Get extra kwargs for AIAgent constructor (base_url, api_key for proxy)."""
        kwargs = {}

        # Cursor proxy for planning roles
        if role in _PLANNING_ROLES and self._cursor_proxy_config:
            if role == AgentRole.ZHONGSHU:
                kwargs["base_url"] = self._cursor_proxy_config.get("base_url", "")
                kwargs["api_key"] = self._cursor_proxy_config.get("api_key", "")

        return kwargs

    def _run_agent(
        self,
        role: AgentRole,
        contract: DelegationContract,
        system_prompt: str,
        toolsets: List[str],
        parent_agent=None,
    ) -> tuple:
        """Create temporary AIAgent, execute task, return (summary, tokens)."""
        hermes_agent_dir = str(Path.home() / ".hermes" / "hermes-agent")
        if hermes_agent_dir not in sys.path:
            sys.path.insert(0, hermes_agent_dir)

        from run_agent import AIAgent

        model = self._get_model_for_role(role, parent_agent)
        extra_kwargs = self._get_agent_kwargs(role, parent_agent)

        agent = AIAgent(
            model=model,
            max_iterations=contract.max_iterations,
            enabled_toolsets=toolsets if toolsets else None,
            ephemeral_system_prompt=system_prompt,
            skip_context_files=True,
            skip_memory=True,
            quiet_mode=True,
            **extra_kwargs,
        )
        try:
            result = agent.run_conversation(
                user_message=f"Execute task: {contract.task}",
                task_id=contract.delegation_id,
            )
            summary = result.get("final_response", "") or ""
            tokens = result.get("api_calls", 0)
            if isinstance(summary, dict):
                summary = json.dumps(summary, ensure_ascii=False)
            return str(summary), tokens
        finally:
            agent.close()

    def _record_and_persist(
        self,
        state: ResidentAgentState,
        contract: DelegationContract,
        summary: str,
        tokens: int,
    ) -> None:
        state.lifecycle = AgentLifecycle.DEACTIVATE.value
        state.total_tasks_completed += 1
        state.total_tokens_consumed += tokens
        state.completed_contracts.append(contract.delegation_id)
        state.memory.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contract_id": contract.delegation_id,
            "summary": summary[:500],
            "outcome": "success" if summary else "empty",
        })
        if len(state.memory) > 20:
            state.memory = state.memory[-20:]
        self._state_store.save_agent_state(state)
        state.lifecycle = AgentLifecycle.IDLE.value

    def _record_failure(
        self,
        state: ResidentAgentState,
        contract: DelegationContract,
        error: str,
    ) -> None:
        state.total_tasks_completed += 1
        state.memory.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contract_id": contract.delegation_id,
            "summary": f"FAILED: {error[:300]}",
            "outcome": "failure",
        })
        if len(state.memory) > 20:
            state.memory = state.memory[-20:]
        self._state_store.save_agent_state(state)

    def _get_toolsets_for_role(self, role: AgentRole) -> List[str]:
        return {
            AgentRole.ZHONGSHU: [],
            AgentRole.MENGXIA: [],
            AgentRole.SHANGSHU: [],
            AgentRole.GONGBU: ["file", "terminal"],
            AgentRole.HUBU: ["file", "web"],
            AgentRole.LIBU: ["file"],
            AgentRole.BINGBU: ["terminal", "file"],
            AgentRole.XINGBU: ["file", "terminal"],
            AgentRole.LIBU_RENSHI: ["file"],
        }.get(role, [])
