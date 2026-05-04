"""Three-stage harness rule compiler: Extract → Normalize → Compile.

Converts harness markdown files into role-trimmed, task-aware governance rules
for injection into agent system prompts. Each rule carries a [rule_id] marker
for mechanical verification.

Architecture:
  Layer 1: CONSTITUTION — hardcoded 7 laws, immutable, all agents
  Layer 2: ROLE POLICY — extracted from md, filtered by role
  Layer 3: TASK CONTEXT — overlay rules based on task type / contract
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import AgentRole, DelegationContract


# ============================================================
# Data Model
# ============================================================

@dataclass
class RuleItem:
    """A single normalized governance rule."""
    id: str                    # e.g. "law.1", "safety.3", "collaboration.1"
    source: str                # e.g. "constitution", "rules/safety.md"
    strength: str              # "never" / "always" / "ask_first" / "should"
    scope: str                 # "all" / "planning" / "production" / ...
    category: str              # "safety" / "communication" / "quality" / ...
    instruction: str           # executable instruction text
    priority: int              # constitution=100, safety=90, quality=70, ...


# ============================================================
# Layer 1: Constitution (hardcoded, immutable)
# ============================================================

CONSTITUTION_LAWS = [
    RuleItem("law.1", "constitution", "never", "all", "safety", priority=100,
             instruction="Never execute destructive operations without explicit human confirmation. "
                         "Destructive: file deletion, db drops, force-push, infra teardown, "
                         "credential revocation."),
    RuleItem("law.2", "constitution", "never", "all", "truthfulness", priority=100,
             instruction="Never fabricate information or hide uncertainty. "
                         "Never invent function signatures, API endpoints, file paths, or config keys."),
    RuleItem("law.3", "constitution", "always", "all", "boundary", priority=100,
             instruction="Stay within your assigned role. Escalate when uncertain, never guess. "
                         "六部 must never bypass 尚书省 to communicate with other 六部."),
    RuleItem("law.4", "constitution", "always", "all", "traceability", priority=100,
             instruction="Every significant decision must be traceable to a rule, "
                         "reasoning chain, or explicit instruction."),
    RuleItem("law.5", "constitution", "always", "all", "noise", priority=100,
             instruction="Prefer pointers over full text. Minimize context noise. "
                         "Before adding to context: 'Does this need to be HERE?'"),
    RuleItem("law.6", "constitution", "always", "all", "learning", priority=100,
             instruction="Record outcomes and update understanding from feedback. "
                         "Compare actual vs expected results."),
    RuleItem("law.7", "constitution", "always", "all", "collaboration", priority=100,
             instruction="Delegation must include: task, success criteria, scope, deadline. "
                         "Receiver must confirm understanding before executing."),
]


# ============================================================
# Role → Group mapping
# ============================================================

_ROLE_GROUPS: Dict[str, Set[AgentRole]] = {
    "planning": {AgentRole.ZHONGSHU, AgentRole.MENGXIA, AgentRole.SHANGSHU},
    "production": {AgentRole.GONGBU, AgentRole.HUBU, AgentRole.LIBU},
    "automation": {AgentRole.BINGBU},
    "verification": {AgentRole.XINGBU},
    "governance": {AgentRole.LIBU_RENSHI},
}

# Which role groups each dynamic rule file applies to
_DYNAMIC_RULE_APPLICABILITY: Dict[str, object] = {
    "rules/safety.md": "all",
    "rules/collaboration.md": "all",
    "rules/quality.md": {"planning", "production", "verification"},
    "rules/lifecycle.md": "all",
    "rules/communication.md": "all",
    "rules/delegation.md": {"planning"},
    "protocols/message-spec.md": "all",
    "protocols/delegation-spec.md": {"planning"},
    "protocols/handshake.md": "all",
}

# Strength ordering for sorting
_STRENGTH_ORDER = {"never": 0, "always": 1, "ask_first": 2, "must": 3, "should": 4}

# Category priority for sorting
_CATEGORY_PRIORITY = {
    "safety": 90, "boundary": 90, "truthfulness": 90,
    "communication": 80, "collaboration": 80,
    "quality": 70, "traceability": 70,
    "lifecycle": 60, "delegation": 60,
    "style": 10,
}

# Strength detection patterns
_STRENGTH_PATTERNS = [
    (r"\bNEVER\b", "never"),
    (r"\bALWAYS\b", "always"),
    (r"\bASK\s+FIRST\b", "ask_first"),
    (r"\bMUST\b", "must"),
    (r"\bSHOULD\b", "should"),
    (r"\b禁止\b", "never"),
    (r"\b必须\b", "must"),
    (r"\b不得\b", "never"),
    (r"\b建议\b", "should"),
]


# ============================================================
# HarnessCompiler
# ============================================================

class HarnessCompiler:
    """Three-stage rule compiler: extract → normalize → compile.

    Converts harness markdown files into role-trimmed governance rules
    for injection into agent system prompts.
    """

    def __init__(self, harness_dir: Path):
        self._harness_dir = Path(harness_dir)
        self._normalized_rules: List[RuleItem] = []
        self._compiled_cache: Dict[str, str] = {}  # "role:task_type" → compiled text

    def initialize(self) -> None:
        """Load all md files, extract and normalize rules. Call once at startup."""
        self._normalized_rules = list(CONSTITUTION_LAWS)
        for md_file in self._iter_rule_files():
            raw_items = self._extract(md_file)
            normalized = self._normalize(raw_items, md_file)
            self._normalized_rules.extend(normalized)
        self._deduplicate()

    def compile_for_role(
        self,
        role: AgentRole,
        task_type: Optional[str] = None,
        contract: Optional[DelegationContract] = None,
    ) -> str:
        """Compile governance rules for a specific role + optional task overlay.

        Returns a prompt block with [rule_id] markers on each rule.
        """
        cache_key = f"{role.value}:{task_type or 'default'}"
        if cache_key in self._compiled_cache:
            return self._compiled_cache[cache_key]

        # Layer 1+2: constitution + role policy
        base_rules = [r for r in self._normalized_rules if self._is_applicable(r, role)]

        # Layer 3: task overlay (always included, not subject to cap)
        overlay_rules = []
        if task_type:
            overlay_rules.extend(self._get_task_overlay(task_type))
        if contract:
            overlay_rules.extend(self._get_contract_overlay(contract))

        # Sort base rules: priority desc, then strength asc (never=0 first)
        base_rules.sort(key=lambda r: (-r.priority, _STRENGTH_ORDER.get(r.strength, 99)))

        # Cap base rules to prevent token overflow (constitution 7 + dynamic ~20)
        base_rules = base_rules[:30]

        # Overlay rules are appended after base (always included)
        applicable = base_rules + overlay_rules

        prompt = self._render(applicable)
        self._compiled_cache[cache_key] = prompt
        return prompt

    @property
    def normalized_rules(self) -> List[RuleItem]:
        """Access normalized rules for testing."""
        return self._normalized_rules

    # --- Stage 1: Extract ---

    def _iter_rule_files(self) -> List[Path]:
        """List all dynamic rule files from harness directory."""
        files = []
        for subdir in ["rules", "protocols"]:
            dir_path = self._harness_dir / subdir
            if dir_path.is_dir():
                for f in sorted(dir_path.glob("*.md")):
                    rel = f"{subdir}/{f.name}"
                    if rel in _DYNAMIC_RULE_APPLICABILITY:
                        files.append(f)
        return files

    # Max rules per source file (prevents prompt bloat)
    _MAX_RULES_PER_FILE = 5

    def _extract(self, md_path: Path) -> List[dict]:
        """Stage 1: Extract raw rule items from a markdown file.

        Conservative extraction — only picks items with strength markers
        or bullets under headings that contain strength markers.
        Limits total items per file to prevent prompt bloat.
        """
        if not md_path.exists():
            return []

        text = md_path.read_text(encoding="utf-8")
        raw_items = []
        current_heading = ""
        current_heading_level = 0
        heading_has_strength = False

        for line in text.split("\n"):
            stripped = line.strip()

            # Track headings
            heading_match = re.match(r"^(#{1,4})\s+(.+)", stripped)
            if heading_match:
                current_heading_level = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                heading_has_strength = self._detect_strength(current_heading) is not None
                continue

            # Skip empty lines and code blocks
            if not stripped or stripped.startswith("```"):
                continue

            # Bullet items — only if heading has strength marker or bullet itself has one
            if re.match(r"^[-*]\s+", stripped):
                content = re.sub(r"^[-*]\s+", "", stripped)
                if not content:
                    continue
                strength = self._detect_strength(content)
                # Only extract if: bullet has strength marker, OR heading has strength marker
                if strength or heading_has_strength:
                    raw_items.append({
                        "text": content,
                        "heading": current_heading,
                        "heading_level": current_heading_level,
                        "strength": strength or self._detect_strength(current_heading),
                        "type": "bullet",
                    })
                continue

            # Table rows with constraint keywords
            if "|" in stripped and self._detect_strength(stripped):
                cells = [c.strip() for c in stripped.split("|") if c.strip()]
                if cells:
                    content = " — ".join(cells)
                    raw_items.append({
                        "text": content,
                        "heading": current_heading,
                        "heading_level": current_heading_level,
                        "strength": self._detect_strength(content),
                        "type": "table",
                    })
                continue

            # Standalone lines with strength markers
            if self._detect_strength(stripped):
                raw_items.append({
                    "text": stripped,
                    "heading": current_heading,
                    "heading_level": current_heading_level,
                    "strength": self._detect_strength(stripped),
                    "type": "line",
                })

        # Limit per file
        return raw_items[:self._MAX_RULES_PER_FILE]

    def _detect_strength(self, text: str) -> Optional[str]:
        """Detect rule strength from text content."""
        for pattern, strength in _STRENGTH_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return strength
        return None

    # --- Stage 2: Normalize ---

    def _normalize(self, raw_items: List[dict], source_path: Path) -> List[RuleItem]:
        """Stage 2: Convert raw extracted items into RuleItem objects."""
        source_name = self._relative_path(source_path)
        category = self._infer_category(source_path)
        scope = self._infer_scope(source_path)
        priority = _CATEGORY_PRIORITY.get(category, 50)

        rules = []
        for i, item in enumerate(raw_items):
            strength = item.get("strength") or "should"
            rule_id = f"{category}.{i + 1}"

            # Truncate overly long instructions
            instruction = item["text"]
            if len(instruction) > 200:
                instruction = instruction[:197] + "..."

            rules.append(RuleItem(
                id=rule_id,
                source=source_name,
                strength=strength,
                scope=scope,
                category=category,
                instruction=instruction,
                priority=priority,
            ))
        return rules

    def _relative_path(self, path: Path) -> str:
        """Get relative path from harness dir."""
        try:
            return str(path.relative_to(self._harness_dir))
        except ValueError:
            return path.name

    def _infer_category(self, path: Path) -> str:
        """Infer rule category from file path and content."""
        name = path.stem.lower()
        category_map = {
            "safety": "safety",
            "collaboration": "collaboration",
            "communication": "communication",
            "quality": "quality",
            "lifecycle": "lifecycle",
            "delegation": "delegation",
            "message-spec": "communication",
            "delegation-spec": "delegation",
            "handshake": "collaboration",
        }
        return category_map.get(name, "general")

    def _infer_scope(self, path: Path) -> str:
        """Infer which role groups this file applies to."""
        rel = self._relative_path(path)
        applicability = _DYNAMIC_RULE_APPLICABILITY.get(rel, "all")
        if applicability == "all":
            return "all"
        # Return first matching group for metadata (actual filtering is role-based)
        return "all"

    def _deduplicate(self) -> None:
        """Remove duplicate rules (keep constitution version when duplicates exist)."""
        seen: Dict[str, RuleItem] = {}
        deduped = []
        for r in self._normalized_rules:
            # Key: first 100 chars of instruction, lowercased
            key = r.instruction.lower().strip()[:100]
            if key in seen:
                existing = seen[key]
                # Keep constitution over dynamic rules
                if existing.source == "constitution":
                    continue
                # Keep higher priority
                if r.priority > existing.priority:
                    deduped.remove(existing)
                    deduped.append(r)
                    seen[key] = r
                continue
            seen[key] = r
            deduped.append(r)
        self._normalized_rules = deduped

    # --- Stage 3: Compile ---

    def _is_applicable(self, rule: RuleItem, role: AgentRole) -> bool:
        """Check if a rule applies to the given role."""
        # Constitution always applies
        if rule.source == "constitution":
            return True
        # Task overlay always applies (filtered at compile time)
        if rule.source == "task_overlay":
            return True
        # Check role group applicability
        rel = rule.source
        applicability = _DYNAMIC_RULE_APPLICABILITY.get(rel, "all")
        if applicability == "all":
            return True
        if isinstance(applicability, set):
            for group_name in applicability:
                if role in _ROLE_GROUPS.get(group_name, set()):
                    return True
        return False

    def _get_task_overlay(self, task_type: str) -> List[RuleItem]:
        """Get task-type-specific overlay rules."""
        overlays = {
            "write_code": [
                RuleItem("task.write.1", "task_overlay", "always", "all", "quality", priority=60,
                         instruction="Code changes must pass validation before submission."),
                RuleItem("task.write.2", "task_overlay", "always", "all", "quality", priority=60,
                         instruction="Prefer editing existing files over creating new ones."),
            ],
            "read_only": [
                RuleItem("task.read.1", "task_overlay", "always", "all", "safety", priority=60,
                         instruction="Read-only task: do not modify any files."),
            ],
            "external_api": [
                RuleItem("task.api.1", "task_overlay", "ask_first", "all", "safety", priority=60,
                         instruction="External API calls require confirmation before execution."),
            ],
            "deploy": [
                RuleItem("task.deploy.1", "task_overlay", "ask_first", "all", "safety", priority=60,
                         instruction="Deployment operations require explicit human confirmation."),
            ],
        }
        return overlays.get(task_type, [])

    def _get_contract_overlay(self, contract: DelegationContract) -> List[RuleItem]:
        """Get contract-specific overlay rules."""
        rules = []
        # If contract has deadline, add time-awareness rule
        if contract.deadline:
            rules.append(RuleItem(
                "contract.deadline.1", "task_overlay", "always", "all", "lifecycle",
                priority=60,
                instruction=f"Task deadline: {contract.deadline}. Prioritize completion.",
            ))
        # If contract has specific authority restrictions
        if contract.authority and "read" in contract.authority and "write" not in contract.authority:
            rules.append(RuleItem(
                "contract.readonly.1", "task_overlay", "never", "all", "safety",
                priority=60,
                instruction="Contract restricts to read-only access. Do not write files.",
            ))
        return rules

    def _render(self, rules: List[RuleItem]) -> str:
        """Stage 3: Render rules into prompt text with [rule_id] markers."""
        if not rules:
            return ""

        lines = ["## Governance Rules (runtime-enforced)\n"]
        current_category = None

        for r in rules:
            if r.category != current_category:
                current_category = r.category
                strength_tag = self._strength_tag(r.strength)
                lines.append(f"\n### {r.category.title()} {strength_tag}")

            lines.append(f"- [{r.id}] {r.instruction}")

        return "\n".join(lines)

    def _strength_tag(self, strength: str) -> str:
        """Get a display tag for strength level."""
        return {
            "never": "(NEVER)",
            "always": "(ALWAYS)",
            "ask_first": "(ASK FIRST)",
            "must": "(MUST)",
            "should": "(SHOULD)",
        }.get(strength, "")
