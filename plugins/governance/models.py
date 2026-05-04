"""Data models for the 三省六部 governance framework."""

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AgentRole(enum.Enum):
    ROOT_AGENT = "root_agent"
    ZHONGSHU = "zhongshu"       # 中书省 — 规划
    MENGXIA = "menxia"          # 门下省 — 审核
    SHANGSHU = "shangshu"       # 尚书省 — 调度
    GONGBU = "gongbu"           # 工部 — 产出型
    HUBU = "hubu"               # 户部 — 数据型
    LIBU = "libu"               # 礼部 — 表达型
    BINGBU = "bingbu"           # 兵部 — 自动化型
    XINGBU = "xingbu"           # 刑部 — 校验型
    LIBU_RENSHI = "libu_renshi" # 吏部 — 治理型


class AgentLifecycle(enum.Enum):
    IDLE = "idle"
    ACTIVATED = "activated"
    EXECUTE = "execute"
    REPORT = "report"
    DEACTIVATE = "deactivate"


class TransactionState(enum.Enum):
    CREATED = "created"
    PLAN = "plan"
    PLAN_COMPLETE = "plan_complete"
    REVIEW = "review"
    REVIEW_COMPLETE = "review_complete"
    DISPATCH = "dispatch"
    DISPATCH_COMPLETE = "dispatch_complete"
    EXECUTE = "execute"
    EXECUTE_COMPLETE = "execute_complete"
    INTEGRATE = "integrate"
    COMPLETE = "complete"
    REJECTED = "rejected"
    ERROR = "error"


@dataclass
class DelegationContract:
    delegation_id: str
    task: str
    success_criteria: List[str]
    context_scope: Dict[str, Any]
    authority: List[str]
    deadline: str
    result_format: Dict[str, Any]
    ministry: str
    max_iterations: int = 3
    priority: str = "normal"
    token_budget: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    revision: int = 0
    notes: str = ""


@dataclass
class ResidentAgentState:
    agent_id: str
    role: str                          # AgentRole.value
    tier: str                          # "ministry" (三省) / "department" (六部)
    lifecycle: str = "idle"            # AgentLifecycle.value
    version: int = 1                   # optimistic lock version
    updated_at: Optional[str] = None   # ISO8601
    active_contract_id: Optional[str] = None  # task lock
    memory: List[Dict[str, Any]] = field(default_factory=list)
    completed_contracts: List[str] = field(default_factory=list)
    total_tokens_consumed: int = 0
    total_tasks_completed: int = 0
    trust_score: float = 1.0
    last_activated: Optional[str] = None


@dataclass
class GovernanceTransaction:
    """A complete governance chain transaction. Serializable for crash recovery."""
    transaction_id: str                # txn_<uuid>
    goal: str
    context: str
    priority: str
    state: str = "created"             # TransactionState.value
    plan: Optional[Dict[str, Any]] = None
    review_verdict: Optional[str] = None   # "approve" / "reject" / "revise"
    review_notes: Optional[str] = None
    revision_count: int = 0
    revision_history: List[Dict[str, Any]] = field(default_factory=list)
    contracts: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    integrated_result: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass
class GovernanceResult:
    status: str                        # "completed" / "rejected" / "error"
    transaction_id: str = ""
    integrated_result: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
