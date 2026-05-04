"""Pluggable task router for 六部 dispatch."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from .models import DelegationContract


class BaseClassifier(ABC):
    """Abstract classifier interface. Implement to provide custom routing."""

    @abstractmethod
    def classify(self, goal: str, context: Optional[str] = None) -> str:
        """Classify a task goal into a ministry name (e.g. 'gongbu')."""
        ...


class KeywordClassifier(BaseClassifier):
    """Default classifier: keyword matching. Covers ~80% of simple cases."""

    RULES = [
        (["code", "write", "build", "implement", "create", "file", "script", "fix", "refactor",
          "代码", "编写", "实现", "创建", "脚本", "修复", "重构", "开发"], "gongbu"),
        (["data", "research", "collect", "analyze", "search", "knowledge", "fetch", "scrape",
          "数据", "搜索", "收集", "分析", "资料", "知识", "查询", "检索"], "hubu"),
        (["report", "summarize", "present", "document", "email", "format", "translate",
          "报告", "总结", "呈现", "文档", "邮件", "格式", "翻译", "汇报"], "libu"),
        (["automate", "workflow", "batch", "tool", "integrate", "pipeline", "deploy",
          "自动化", "工作流", "批量", "工具", "集成", "流水线", "部署", "联动"], "bingbu"),
        (["test", "validate", "security", "check", "verify", "audit", "lint", "review",
          "测试", "验证", "安全", "检查", "审计", "校验", "风险"], "xingbu"),
        (["track", "priority", "status", "manage", "govern", "assign", "schedule",
          "跟踪", "优先级", "状态", "管理", "治理", "分配", "调度", "流程"], "libu_renshi"),
    ]

    def classify(self, goal: str, context: Optional[str] = None) -> str:
        combined = f"{goal} {context or ''}".lower()
        scores: Dict[str, int] = {}
        for keywords, ministry in self.RULES:
            for kw in keywords:
                if kw in combined:
                    # Longer keywords get higher weight (2+ chars = 2 points)
                    weight = 2 if len(kw) >= 2 else 1
                    scores[ministry] = scores.get(ministry, 0) + weight
        return max(scores, key=scores.get) if scores else "gongbu"


class LLMClassifier(BaseClassifier):
    """Optional classifier using LLM for intent parsing. Future implementation."""

    def classify(self, goal: str, context: Optional[str] = None) -> str:
        raise NotImplementedError("LLM classifier not yet implemented")


class MinistryRouter:
    """
    Pluggable task router.
    Default uses KeywordClassifier; swap in LLMClassifier or custom impl.
    """

    def __init__(self, classifier: Optional[BaseClassifier] = None):
        self._classifier = classifier or KeywordClassifier()

    def classify_task(self, goal: str, context: Optional[str] = None) -> str:
        """Classify task into a ministry name."""
        return self._classifier.classify(goal, context)

    def split_tasks(self, goal: str, context: Optional[str] = None) -> List[DelegationContract]:
        """尚书省 core: split a goal into delegation contracts."""
        ministry = self.classify_task(goal, context)
        return [DelegationContract(
            delegation_id=f"del_{datetime.now().strftime('%Y%m%d')}_{uuid4().hex[:6]}",
            task=goal,
            success_criteria=["任务完成"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read", "write_files"],
            deadline=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            result_format={"type": "text"},
            ministry=ministry,
        )]
