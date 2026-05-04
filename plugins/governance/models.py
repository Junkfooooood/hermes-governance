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
    INTERVIEW = "interview"               # Deep Interview (中书省澄清)
    INTERVIEW_COMPLETE = "interview_complete"
    PLAN = "plan"
    PLAN_COMPLETE = "plan_complete"
    REVIEW = "review"
    REVIEW_SPEC_COMPLETE = "review_spec_complete"    # spec compliance 完成
    REVIEW_QUALITY = "review_quality"                 # code quality 审核
    REVIEW_QUALITY_COMPLETE = "review_quality_complete"
    DECOMPOSE = "decompose"                           # 任务分解
    DECOMPOSE_COMPLETE = "decompose_complete"
    DISPATCH = "dispatch"
    DISPATCH_COMPLETE = "dispatch_complete"
    EXECUTE = "execute"
    EXECUTE_COMPLETE = "execute_complete"
    VERIFY = "verify"                                 # 刑部验证
    VERIFY_COMPLETE = "verify_complete"
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
class InterviewRecord:
    """Deep Interview 问答记录。"""
    questions: List[Dict[str, str]] = field(default_factory=list)
    # [{"question": "...", "answer": "...", "timestamp": "..."}]
    clarity_score: float = 0.0         # 0-1, 需求清晰度
    assumptions: List[str] = field(default_factory=list)
    confirmed: bool = False


@dataclass
class BoulderState:
    """
    项目状态跟踪 — 类似 OMC 的 Boulder State。
    记录当前有哪些任务在进行、哪些被阻塞、哪些已完成。
    """
    active_goals: List[Dict[str, Any]] = field(default_factory=list)
    blocked_goals: List[Dict[str, Any]] = field(default_factory=list)
    completed_goals: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: str = ""


@dataclass
class DecisionLog:
    """决策日志 — 记录每次治理链的决策过程和结果。"""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    # [{"txn_id": "...", "goal": "...", "verdict": "...", "plan_summary": "...",
    #   "outcome": "...", "lessons": "...", "timestamp": "..."}]


@dataclass
class NotepadWisdom:
    """
    教训记忆 — agent 执行过程中发现的模式、陷阱、最佳实践。
    类似 OMC 的 Notepad Wisdom。
    """
    patterns: List[Dict[str, str]] = field(default_factory=list)
    # [{"pattern": "...", "context": "...", "discovered_by": "...", "timestamp": "..."}]


@dataclass
class GovernanceTransaction:
    """A complete governance chain transaction. Serializable for crash recovery."""
    transaction_id: str                # txn_<uuid>
    goal: str
    context: str
    priority: str
    state: str = "created"             # TransactionState.value
    interview: Optional[Dict[str, Any]] = None       # Deep Interview 结果
    plan: Optional[Dict[str, Any]] = None
    review_verdict: Optional[str] = None   # "approve" / "reject" / "revise"
    review_notes: Optional[str] = None
    spec_review: Optional[Dict[str, Any]] = None      # spec compliance 审核结果
    quality_review: Optional[Dict[str, Any]] = None    # code quality 审核结果
    revision_count: int = 0
    revision_history: List[Dict[str, Any]] = field(default_factory=list)
    sub_tasks: List[Dict[str, Any]] = field(default_factory=list)    # 分解后的子任务
    contracts: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    verify_result: Optional[Dict[str, Any]] = None    # 刑部验证结果
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
