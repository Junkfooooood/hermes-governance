"""Mechanical rule validator — Sensors for governance feedback.

Validates:
1. System prompt completeness (constitution markers, role rules, token budget)
2. Agent output compliance (boundary violations, secret leaks, lateral comms)

Uses [rule_id] markers in compiled prompts for reliable detection
instead of fragile string matching.
"""

import re
from typing import Dict, List, Optional, Set

from .models import AgentRole, DelegationContract, ValidationResult

# Six ministries (六部) — for lateral communication checks
_LIUBU_ROLES = {
    AgentRole.GONGBU, AgentRole.HUBU, AgentRole.LIBU,
    AgentRole.BINGBU, AgentRole.XINGBU, AgentRole.LIBU_RENSHI,
}

# Ministry names for lateral communication detection
_MINISTRY_NAMES = {
    AgentRole.GONGBU: {"gongbu", "工部"},
    AgentRole.HUBU: {"hubu", "户部"},
    AgentRole.LIBU: {"libu", "礼部"},
    AgentRole.BINGBU: {"bingbu", "兵部"},
    AgentRole.XINGBU: {"xingbu", "刑部"},
    AgentRole.LIBU_RENSHI: {"libu_renshi", "吏部"},
}

# Forbidden tools per role (safety boundary)
_FORBIDDEN_TOOLS: Dict[AgentRole, Set[str]] = {
    AgentRole.BINGBU: {"governance_committee"},  # 兵部不能调用治理工具
    AgentRole.HUBU: {"terminal"},                 # 户部主要做数据收集
    AgentRole.LIBU: {"terminal"},                 # 礼部主要做报告
    AgentRole.LIBU_RENSHI: {"terminal"},          # 吏部主要做治理跟踪
}

# Secret patterns to detect leaks
_SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|token|password|credential)\s*[:=]\s*\S+",
    r"(?i)sk-[a-zA-Z0-9]{20,}",           # OpenAI-style keys
    r"(?i)ghp_[a-zA-Z0-9]{36,}",           # GitHub tokens
    r"(?i)xoxb-[a-zA-Z0-9-]+",            # Slack tokens
    r"-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----",
]


class RuleValidator:
    """Mechanical governance rule validator.

    Acts as Sensors in the feedforward/feedback loop:
    - validate_system_prompt(): pre-flight check before agent execution
    - validate_agent_output(): post-execution compliance check
    """

    # Layered token budget
    TOKEN_BUDGET: Dict[str, int] = {
        "constitution": 300,
        "role_rules": 400,
        "task_overlay": 200,
        "total": 1000,
    }

    # Constitution rule IDs that must always be present
    _CONSTITUTION_IDS = {f"law.{i}" for i in range(1, 8)}

    # Role-specific required rule categories
    _ROLE_REQUIRED_CATEGORIES: Dict[AgentRole, Set[str]] = {
        AgentRole.ZHONGSHU: {"collaboration"},
        AgentRole.MENGXIA: {"safety", "quality"},
        AgentRole.SHANGSHU: {"collaboration"},
        AgentRole.GONGBU: {"safety"},
        AgentRole.HUBU: {"safety"},
        AgentRole.LIBU: {"communication"},
        AgentRole.BINGBU: {"safety", "boundary"},
        AgentRole.XINGBU: {"safety", "quality"},
        AgentRole.LIBU_RENSHI: {"collaboration"},
    }

    def validate_system_prompt(
        self,
        role: AgentRole,
        prompt: str,
    ) -> ValidationResult:
        """Validate that system prompt contains required governance rules.

        Uses [rule_id] markers for reliable detection.
        """
        checks: List[str] = []

        # Check 1: Constitution 7 laws — via [law.1] ~ [law.7] markers
        for rule_id in self._CONSTITUTION_IDS:
            marker = f"[{rule_id}]"
            if marker not in prompt:
                checks.append(f"Missing constitution marker: {marker}")

        # Check 2: Role-required rule categories
        required_cats = self._ROLE_REQUIRED_CATEGORIES.get(role, set())
        for cat in required_cats:
            # Look for category heading (### Category)
            if f"### {cat.title()}" not in prompt and f"### {cat.upper()}" not in prompt:
                checks.append(f"Missing rule category: {cat}")

        # Check 3: Layered token budget
        token_count = self._estimate_tokens(prompt)
        if token_count > self.TOKEN_BUDGET["total"]:
            checks.append(f"Total token overflow: {token_count} > {self.TOKEN_BUDGET['total']}")

        return ValidationResult(
            passed=len(checks) == 0,
            issues=checks,
            token_count=token_count,
        )

    def validate_agent_output(
        self,
        role: AgentRole,
        result: dict,
        contract: Optional[DelegationContract] = None,
    ) -> List[str]:
        """Validate agent output against governance rules.

        Checks full output (raw output, tool calls, messages), not just summary.
        Returns list of violation descriptions.
        """
        violations: List[str] = []

        # Extract full output for comprehensive checking
        full_output = self._extract_full_output(result)

        # Check 1: Bingbu boundary violations
        if role == AgentRole.BINGBU:
            markers = ["COMPLETE", "REJECTED", "APPROVED", "状态已更新", "任务完成",
                       "状态已迁移", "governance state"]
            for marker in markers:
                if marker in full_output:
                    violations.append(
                        f"bingbu.boundary: governance state marker '{marker}' found in output"
                    )
                    break

        # Check 2: Secret/credential leaks
        if self._contains_secrets(full_output):
            violations.append("safety.leak: potential secrets or credentials in output")

        # Check 3: Lateral communication (六部 referencing other ministries)
        if role in _LIUBU_ROLES:
            mentioned = self._mentions_other_ministries(full_output, role)
            if mentioned:
                violations.append(
                    f"communication.lateral: {role.value} references {mentioned} directly"
                )

        # Check 4: Forbidden tool usage
        forbidden = _FORBIDDEN_TOOLS.get(role, set())
        for tc in result.get("tool_calls", []):
            tool_name = tc.get("tool", "") if isinstance(tc, dict) else ""
            if tool_name in forbidden:
                violations.append(f"safety.forbidden_tool: {tool_name} not allowed for {role.value}")

        # Check 5: Contract scope violations
        if contract:
            scope_violations = self._check_contract_scope(full_output, contract)
            violations.extend(scope_violations)

        return violations

    def _extract_full_output(self, result: dict) -> str:
        """Extract complete output text for validation.

        Priority: raw_output > messages > summary.
        Includes tool call inputs for comprehensive checking.
        """
        parts: List[str] = []

        # Priority 1: Full natural language output
        if result.get("raw_output"):
            parts.append(result["raw_output"])

        # Priority 2: Message body
        for msg in result.get("messages", []):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                content = msg.get("content", "")
                if content:
                    parts.append(content)

        # Fallback: summary
        if not parts:
            parts.append(result.get("summary", ""))

        # Include tool call inputs
        for tc in result.get("tool_calls", []):
            if isinstance(tc, dict) and tc.get("input"):
                parts.append(str(tc["input"]))

        return "\n".join(parts)

    def _contains_secrets(self, text: str) -> bool:
        """Check if text contains potential secrets or credentials."""
        for pattern in _SECRET_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def _mentions_other_ministries(self, text: str, current_role: AgentRole) -> Optional[str]:
        """Check if a 六部 agent references other ministries directly."""
        text_lower = text.lower()

        for role, names in _MINISTRY_NAMES.items():
            if role == current_role:
                continue
            for name in names:
                if name.lower() in text_lower:
                    return name
        return None

    def _check_contract_scope(self, output: str, contract: DelegationContract) -> List[str]:
        """Check if output violates contract scope restrictions."""
        violations: List[str] = []

        # Check authority restrictions
        if contract.authority:
            if "read" in contract.authority and "write" not in contract.authority:
                # Read-only contract: check for file modification indicators
                write_indicators = ["wrote ", "modified ", "created file", "saved to",
                                    "写入", "修改", "创建文件"]
                for indicator in write_indicators:
                    if indicator in output.lower():
                        violations.append(
                            f"contract.scope: write operation detected in read-only contract "
                            f"(indicator: '{indicator}')"
                        )
                        break

        return violations

    def _estimate_tokens(self, text: str) -> int:
        """Token estimate: CJK chars ~1.5 tokens each, ASCII ~0.25 tokens each."""
        cjk = sum(1 for c in text if ord(c) > 0x4E00)
        ascii_chars = len(text) - cjk
        return int(cjk * 1.5 + ascii_chars * 0.25)
