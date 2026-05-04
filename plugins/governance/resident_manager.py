"""Resident Agent Manager — manages agent lifecycle for 三省六部.

"Resident" means: persistent identity, memory, permissions on disk.
NOT: permanently-running Python objects or background workers.

Agents are activated on-demand: load state → create AIAgent → execute → persist state → release.
"""

import json
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

# Role → tier mapping
_ROLE_TIER = {
    AgentRole.ZHONGSHU: "ministry",
    AgentRole.MENGXIA: "ministry",
    AgentRole.SHANGSHU: "ministry",
    AgentRole.GONGBU: "department",
    AgentRole.HUBU: "department",
    AgentRole.LIBU: "department",
    AgentRole.BINGBU: "department",
    AgentRole.XINGBU: "department",
    AgentRole.LIBU_RENSHI: "department",
}


class ResidentAgentManager:
    """Manages resident agent lifecycle: load → activate → execute → persist → release."""

    def __init__(
        self,
        harness_dir: Optional[Path] = None,
        state_dir: Optional[Path] = None,
        model: Optional[str] = None,
    ):
        self._harness_dir = harness_dir or Path.home() / ".hermes" / "harness"
        self._state_store = GovernanceStateStore(state_dir)
        self._model = model or ""
        self._role_prompts: Dict[str, str] = {}

    @property
    def state_store(self) -> GovernanceStateStore:
        return self._state_store

    def initialize(self) -> None:
        """Load role definitions from harness/roles/*.md."""
        roles_dir = self._harness_dir / "roles"
        for role, filename in _ROLE_FILE_MAP.items():
            path = roles_dir / filename
            if path.exists():
                self._role_prompts[role.value] = path.read_text()
            else:
                self._role_prompts[role.value] = f"You are {role.value}. Perform your assigned duties."

    def activate_agent(
        self,
        role: AgentRole,
        contract: DelegationContract,
        parent_agent=None,
    ) -> Dict[str, Any]:
        """
        Activate a resident agent to execute a contract.

        Flow:
        1. Load agent state from disk
        2. Build system prompt (role def + accumulated memory + contract)
        3. Create temporary AIAgent
        4. Execute run_conversation()
        5. Persist state with version control
        """
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
        """Load state and mark as ACTIVATED."""
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
        """Build system prompt: role definition + memory + contract."""
        parts = []

        # 1. Role definition from harness
        role_prompt = self._role_prompts.get(role.value, "")
        if role_prompt:
            parts.append(role_prompt)

        # 2. Accumulated memory (last 5 entries for context)
        if state.memory:
            recent = state.memory[-5:]
            memory_text = "\n".join(
                f"- [{m.get('timestamp', '?')[:10]}] {m.get('summary', '')}"
                for m in recent
            )
            parts.append(f"\n## Your Recent Memory\n{memory_text}")

        # 3. Contract details
        parts.append(f"\n## Current Task\n{contract.task}")
        if contract.success_criteria:
            criteria = "\n".join(f"- {c}" for c in contract.success_criteria)
            parts.append(f"\n## Success Criteria\n{criteria}")
        if contract.notes:
            parts.append(f"\n## Additional Context\n{contract.notes}")

        # 4. Bingbu hard constraint reminder
        if role == AgentRole.BINGBU:
            parts.append(
                "\n## Hard Constraints (兵部)\n"
                "- You may ONLY produce execution process, NOT final deliverables.\n"
                "- You may ONLY modify execution path, NOT governance state.\n"
                "- Any result aggregation, state transition, or completion judgment "
                "MUST be handled by 尚书省 or 吏部.\n"
                "- Your output should describe what workflows you orchestrated, "
                "what external tools you invoked, and what intermediate results were produced."
            )

        return "\n".join(parts)

    def _run_agent(
        self,
        role: AgentRole,
        contract: DelegationContract,
        system_prompt: str,
        toolsets: List[str],
        parent_agent=None,
    ) -> tuple:
        """Create temporary AIAgent, execute task, return (summary, tokens)."""
        import sys

        # Ensure hermes-agent is importable
        hermes_agent_dir = str(Path.home() / ".hermes" / "hermes-agent")
        if hermes_agent_dir not in sys.path:
            sys.path.insert(0, hermes_agent_dir)

        from run_agent import AIAgent

        # Inherit model from parent if not overridden
        model = self._model
        if not model and parent_agent:
            model = getattr(parent_agent, "model", "")

        agent = AIAgent(
            model=model,
            max_iterations=contract.max_iterations,
            enabled_toolsets=toolsets if toolsets else None,
            ephemeral_system_prompt=system_prompt,
            skip_context_files=True,
            skip_memory=True,
            quiet_mode=True,
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
        """Record result and persist state."""
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
        # Keep memory bounded
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
        """Record failure and persist state."""
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
        """
        Role → toolset mapping.

        三省: reasoning only, no tools.
        六部: each holds domain-specific toolsets.
        兵部: hard constraint — only execution process, no deliverables.
        """
        return {
            AgentRole.ZHONGSHU: [],                     # reasoning only
            AgentRole.MENGXIA: [],                      # reasoning only
            AgentRole.SHANGSHU: [],                     # reasoning only
            AgentRole.GONGBU: ["file", "terminal"],      # 产出型
            AgentRole.HUBU: ["file", "web"],              # 数据型
            AgentRole.LIBU: ["file"],                     # 表达型
            AgentRole.BINGBU: ["terminal", "file"],       # 自动化型 (hard constraint in Decision 1)
            AgentRole.XINGBU: ["file", "terminal"],       # 校验型
            AgentRole.LIBU_RENSHI: ["file"],              # 治理型
        }.get(role, [])
