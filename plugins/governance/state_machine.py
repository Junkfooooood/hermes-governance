"""Governance chain state machine — core logic for 三省六部.

Stages (with all optimizations):
  INTERVIEW → PLAN → REVIEW_SPEC → REVIEW_QUALITY → DECOMPOSE → DISPATCH → EXECUTE → VERIFY → INTEGRATE

Each state transition is independent, testable, and recoverable.
"""

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4

from .feedback_tracker import FeedbackTracker
from .ministry_router import MinistryRouter
from .models import (
    AgentRole,
    DelegationContract,
    GovernanceTransaction,
    TransactionState,
)
from .resident_manager import ResidentAgentManager
from .state_store import GovernanceStateStore


def _deadline(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


class GovernanceStateMachine:
    """Governance chain state machine. Each step independently testable."""

    MAX_RETRIES = 1
    ACCEPT_PARTIAL = True
    MAX_VERIFY_RETRIES = 2  # 刑部验证失败最多重试 2 次

    def __init__(self, manager: ResidentAgentManager, router: MinistryRouter, event_callback=None):
        self._manager = manager
        self._router = router
        self._store: GovernanceStateStore = manager.state_store
        self._validator = manager.rule_validator
        self._feedback = FeedbackTracker(self._store._state_dir)
        self._event_callback = event_callback

    def create_transaction(
        self, goal: str, context: str, priority: str
    ) -> GovernanceTransaction:
        txn = GovernanceTransaction(
            transaction_id=f"txn_{uuid4().hex[:12]}",
            goal=goal,
            context=context,
            priority=priority,
            state=TransactionState.CREATED.value,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._store.save_transaction(txn)
        if self._event_callback:
            self._event_callback(
                txn_id=txn.transaction_id,
                event_type="transaction.created",
                payload={"goal": txn.goal, "priority": txn.priority, "state": txn.state},
            )
        return txn

    def advance(
        self, txn: GovernanceTransaction, parent_agent=None
    ) -> GovernanceTransaction:
        """Advance transaction to terminal state with crash recovery."""
        terminal = {
            TransactionState.COMPLETE.value,
            TransactionState.REJECTED.value,
            TransactionState.ERROR.value,
        }
        while txn.state not in terminal:
            handler = self._get_handler(txn.state)
            try:
                txn = handler(txn, parent_agent)
                self._store.save_transaction(txn)
                if self._event_callback:
                    self._event_callback(
                        txn_id=txn.transaction_id,
                        event_type="state.transition",
                        payload={"state": txn.state, "step": handler.__name__},
                    )
            except Exception as e:
                txn.state = TransactionState.ERROR.value
                txn.audit_trail.append({"step": txn.state, "error": str(e)})
                self._store.save_transaction(txn)
                if self._event_callback:
                    self._event_callback(
                        txn_id=txn.transaction_id,
                        event_type="transaction.error",
                        payload={"error": str(e), "state": txn.state},
                    )
                break
        return txn

    # --- Single-step interfaces ---

    def step_interview(self, txn, parent_agent=None):
        return self._step_interview(txn, parent_agent)

    def step_plan(self, txn, parent_agent=None):
        return self._step_plan(txn, parent_agent)

    def step_review_spec(self, txn, parent_agent=None):
        return self._step_review_spec(txn, parent_agent)

    def step_review_quality(self, txn, parent_agent=None):
        return self._step_review_quality(txn, parent_agent)

    def step_decompose(self, txn, parent_agent=None):
        return self._step_decompose(txn, parent_agent)

    def step_dispatch(self, txn, parent_agent=None):
        return self._step_dispatch(txn, parent_agent)

    def step_execute(self, txn, parent_agent=None):
        return self._step_execute(txn, parent_agent)

    def step_verify(self, txn, parent_agent=None):
        return self._step_verify(txn, parent_agent)

    def step_integrate(self, txn, parent_agent=None):
        return self._step_integrate(txn, parent_agent)

    # --- Handler dispatch ---

    def _get_handler(self, state: str):
        return {
            TransactionState.CREATED.value: self._step_interview,
            TransactionState.INTERVIEW_COMPLETE.value: self._step_plan,
            TransactionState.PLAN_COMPLETE.value: self._step_review_spec,
            TransactionState.REVIEW_SPEC_COMPLETE.value: self._step_review_quality,
            TransactionState.REVIEW_QUALITY_COMPLETE.value: self._step_decompose,
            TransactionState.DECOMPOSE_COMPLETE.value: self._step_dispatch,
            TransactionState.DISPATCH_COMPLETE.value: self._step_execute,
            TransactionState.EXECUTE_COMPLETE.value: self._step_verify,
            TransactionState.VERIFY_COMPLETE.value: self._step_integrate,
        }.get(state, self._step_error)

    # ============================================================
    # STEP 1: Deep Interview (中书省 — 先问后做)
    # ============================================================

    def _step_interview(self, txn, parent_agent) -> GovernanceTransaction:
        """
        中书省 Deep Interview: 在规划前先澄清需求。
        类似 superpowers 的 brainstorming，通过苏格拉底式提问暴露隐含假设。
        """
        txn.state = TransactionState.INTERVIEW.value

        contract = DelegationContract(
            delegation_id=f"interview_{txn.transaction_id}",
            task=(
                "你是一个需求澄清专家。在开始规划之前，你需要通过提问来理解用户的真实需求。\n\n"
                f"用户需求：{txn.goal}\n"
                f"背景信息：{txn.context}\n\n"
                "请执行以下步骤：\n"
                "1. 分析需求中的模糊点和隐含假设\n"
                "2. 提出 3-5 个关键澄清问题\n"
                "3. 基于已有信息给出初步假设\n"
                "4. 输出 JSON 格式：\n"
                '   {"questions": ["q1", "q2", ...], "assumptions": ["a1", ...], '
                '"clarity_score": 0.0-1.0, "ready_to_plan": true/false}\n\n'
                "如果需求已经足够清晰（clarity_score >= 0.8），设置 ready_to_plan=true。"
            ),
            success_criteria=["输出包含 questions、assumptions、clarity_score 的 JSON"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=3),
            result_format={"type": "json"},
            ministry="zhongshu",
            priority=txn.priority,
        )
        result = self._manager.activate_agent(AgentRole.ZHONGSHU, contract, parent_agent)

        # Parse interview result
        interview = self._parse_json_result(result.get("summary", ""))
        txn.interview = {
            "questions": interview.get("questions", []),
            "assumptions": interview.get("assumptions", []),
            "clarity_score": interview.get("clarity_score", 0.5),
            "ready_to_plan": interview.get("ready_to_plan", True),
        }
        txn.state = TransactionState.INTERVIEW_COMPLETE.value
        txn.audit_trail.append({
            "step": "interview", "action": "complete",
            "clarity_score": txn.interview["clarity_score"],
            "question_count": len(txn.interview["questions"]),
        })
        return txn

    # ============================================================
    # STEP 2: Plan (中书省)
    # ============================================================

    def _step_plan(self, txn, parent_agent) -> GovernanceTransaction:
        """中书省: planning with interview context."""
        txn.state = TransactionState.PLAN.value

        # Build enhanced task with interview context
        interview_ctx = ""
        if txn.interview:
            assumptions = txn.interview.get("assumptions", [])
            if assumptions:
                interview_ctx = f"\n已确认的假设：\n" + "\n".join(f"- {a}" for a in assumptions)

        contract = DelegationContract(
            delegation_id=f"plan_{txn.transaction_id}",
            task=f"设计执行方案：{txn.goal}{interview_ctx}",
            success_criteria=["产出清晰的执行步骤和验证方法"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=5),
            result_format={"type": "json"},
            ministry="zhongshu",
            priority=txn.priority,
            notes=txn.context,
        )
        result = self._manager.activate_agent(AgentRole.ZHONGSHU, contract, parent_agent)
        txn.plan = result
        txn.state = TransactionState.PLAN_COMPLETE.value
        txn.audit_trail.append({"step": "zhongshu", "action": "plan_complete"})
        return txn

    # ============================================================
    # STEP 3: Review — Spec Compliance (门下省 第一轮)
    # ============================================================

    def _step_review_spec(self, txn, parent_agent) -> GovernanceTransaction:
        """
        门下省第一轮审核：spec compliance — 计划是否符合需求。
        reject → 终止 | revise → 回到 PLAN | approve → 进入 quality review
        """
        txn.state = TransactionState.REVIEW.value

        contract = DelegationContract(
            delegation_id=f"review_spec_{txn.transaction_id}_r{txn.revision_count}",
            task=(
                "你是一个规格合规审核官。审核执行方案是否符合原始需求。\n\n"
                f"原始需求：{txn.goal}\n"
                f"执行方案：{json.dumps(txn.plan, ensure_ascii=False) if txn.plan else '无'}\n\n"
                "审核维度：\n"
                "1. 方案是否覆盖了需求的所有关键点\n"
                "2. 成功标准是否可验证\n"
                "3. 是否有遗漏的边界条件\n\n"
                '输出 JSON：{"verdict": "approve|reject|revise", "notes": "审核意见", '
                '"missing_items": ["..."], "score": 0.0-1.0}'
            ),
            success_criteria=["输出包含 verdict 的 JSON"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=3),
            result_format={"type": "json"},
            ministry="menxia",
            priority=txn.priority,
        )
        result = self._manager.activate_agent(AgentRole.MENGXIA, contract, parent_agent)

        parsed = self._parse_verdict(result.get("summary", ""))
        txn.spec_review = parsed
        txn.review_verdict = parsed["verdict"]
        txn.review_notes = parsed.get("notes", "")

        if parsed["verdict"] == "reject":
            txn.state = TransactionState.REJECTED.value
            txn.audit_trail.append({"step": "menxia_spec", "action": "rejected", "reason": txn.review_notes})
        elif parsed["verdict"] == "revise" and txn.revision_count < 3:
            txn.revision_history.append({
                "round": txn.revision_count + 1,
                "stage": "spec_review",
                "reason": txn.review_notes,
                "plan_snapshot": txn.plan,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            txn.revision_count += 1
            txn.state = TransactionState.CREATED.value  # back to interview+plan
            txn.audit_trail.append({
                "step": "menxia_spec", "action": "revise",
                "round": txn.revision_count, "reason": txn.review_notes,
            })
        else:
            txn.state = TransactionState.REVIEW_SPEC_COMPLETE.value
            txn.audit_trail.append({"step": "menxia_spec", "action": "approved"})
        return txn

    # ============================================================
    # STEP 4: Review — Code Quality (门下省 第二轮)
    # ============================================================

    def _step_review_quality(self, txn, parent_agent) -> GovernanceTransaction:
        """
        门下省第二轮审核：code quality — 方案的可行性和质量。
        这是 spec compliance 通过后的质量把关。
        """
        txn.state = TransactionState.REVIEW_QUALITY.value

        contract = DelegationContract(
            delegation_id=f"review_quality_{txn.transaction_id}",
            task=(
                "你是一个质量审核官。审核执行方案的可行性和工程质量。\n\n"
                f"执行方案：{json.dumps(txn.plan, ensure_ascii=False) if txn.plan else '无'}\n\n"
                "审核维度：\n"
                "1. 每个步骤是否足够具体（2-5分钟可完成）\n"
                "2. 是否有隐含依赖或循环依赖\n"
                "3. 风险点和缓解措施\n"
                "4. 是否符合 YAGNI 原则（不过度设计）\n\n"
                '输出 JSON：{"verdict": "approve|revise", "notes": "质量意见", '
                '"risks": ["..."], "suggestions": ["..."]}'
            ),
            success_criteria=["输出包含 verdict 的 JSON"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=3),
            result_format={"type": "json"},
            ministry="menxia",
            priority=txn.priority,
        )
        result = self._manager.activate_agent(AgentRole.MENGXIA, contract, parent_agent)

        parsed = self._parse_verdict(result.get("summary", ""))
        txn.quality_review = parsed

        if parsed["verdict"] == "revise" and txn.revision_count < 3:
            txn.revision_history.append({
                "round": txn.revision_count + 1,
                "stage": "quality_review",
                "reason": parsed.get("notes", ""),
                "plan_snapshot": txn.plan,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            txn.revision_count += 1
            txn.state = TransactionState.PLAN_COMPLETE.value  # back to plan (skip interview)
            txn.audit_trail.append({
                "step": "menxia_quality", "action": "revise",
                "round": txn.revision_count, "reason": parsed.get("notes", ""),
            })
        else:
            txn.state = TransactionState.REVIEW_QUALITY_COMPLETE.value
            txn.audit_trail.append({"step": "menxia_quality", "action": "approved"})
        return txn

    # ============================================================
    # STEP 5: Task Decomposer (尚书省 — 拆解原子任务)
    # ============================================================

    def _step_decompose(self, txn, parent_agent) -> GovernanceTransaction:
        """
        尚书省任务分解：将大计划拆解为原子任务（每个 2-5 分钟）。
        类似 OMC 的 task-decomposer 和 superpowers 的 writing-plans。
        """
        txn.state = TransactionState.DECOMPOSE.value

        contract = DelegationContract(
            delegation_id=f"decompose_{txn.transaction_id}",
            task=(
                "你是一个任务分解专家。将执行方案拆解为原子任务。\n\n"
                f"执行方案：{json.dumps(txn.plan, ensure_ascii=False) if txn.plan else '无'}\n"
                f"原始需求：{txn.goal}\n\n"
                "分解原则：\n"
                "1. 每个子任务 2-5 分钟可完成\n"
                "2. 每个子任务有明确的输入/输出\n"
                "3. 标注依赖关系（哪些任务可以并行，哪些必须串行）\n"
                "4. 每个子任务指定最适合的六部\n\n"
                '输出 JSON：{"sub_tasks": [\n'
                '  {"id": "t1", "task": "...", "ministry": "gongbu|hubu|...", '
                '"depends_on": [], "estimated_minutes": 3, '
                '"success_criteria": "..."}\n'
                ']}'
            ),
            success_criteria=["输出包含 sub_tasks 数组的 JSON"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=5),
            result_format={"type": "json"},
            ministry="shangshu",
            priority=txn.priority,
        )
        result = self._manager.activate_agent(AgentRole.SHANGSHU, contract, parent_agent)

        decomposed = self._parse_json_result(result.get("summary", ""))
        txn.sub_tasks = decomposed.get("sub_tasks", [])

        # Fallback: if decomposition fails, create single task from goal
        if not txn.sub_tasks:
            txn.sub_tasks = [{
                "id": "t1",
                "task": txn.goal,
                "ministry": self._router.classify_task(txn.goal, txn.context),
                "depends_on": [],
                "estimated_minutes": 30,
                "success_criteria": "任务完成",
            }]

        txn.state = TransactionState.DECOMPOSE_COMPLETE.value
        txn.audit_trail.append({
            "step": "shangshu", "action": "decomposed",
            "sub_task_count": len(txn.sub_tasks),
        })
        return txn

    # ============================================================
    # STEP 6: Dispatch (尚书省 — 分派合同)
    # ============================================================

    def _step_dispatch(self, txn, parent_agent) -> GovernanceTransaction:
        """尚书省: convert sub_tasks into delegation contracts."""
        txn.state = TransactionState.DISPATCH.value

        contracts = []
        for st in txn.sub_tasks:
            ministry = st.get("ministry", self._router.classify_task(st.get("task", ""), txn.context))
            contract = DelegationContract(
                delegation_id=f"del_{txn.transaction_id}_{st.get('id', uuid4().hex[:6])}",
                task=st.get("task", txn.goal),
                success_criteria=[st.get("success_criteria", "任务完成")],
                context_scope={"files": [], "memory_pointers": []},
                authority=["read", "write_files"],
                deadline=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                result_format={"type": "text"},
                ministry=ministry,
                dependencies=st.get("depends_on", []),
                notes=f"Parent txn: {txn.transaction_id}",
            )
            contracts.append(contract)

        txn.contracts = [asdict(c) for c in contracts]
        txn.state = TransactionState.DISPATCH_COMPLETE.value
        txn.audit_trail.append({
            "step": "shangshu", "action": f"dispatched {len(contracts)} contract(s)",
        })
        return txn

    # ============================================================
    # STEP 7: Execute (六部 — parallel by dependency level)
    # ============================================================

    def _step_execute(self, txn, parent_agent) -> GovernanceTransaction:
        """六部: execute contracts in parallel by dependency level.

        Contracts are grouped into levels via topological sort:
        - Level 0: no dependencies (can all run in parallel)
        - Level 1: depends only on level 0 tasks (run after level 0 completes)
        - Level N: depends on tasks in levels 0..N-1

        Within each level, contracts execute concurrently via ThreadPoolExecutor.
        Different ministries can hold task locks simultaneously (locks are per-role).
        """
        txn.state = TransactionState.EXECUTE.value

        levels = self._build_dependency_levels(txn.contracts)
        executed_ids = set()
        results_lock = threading.Lock()  # protect txn.results and txn.audit_trail

        for level_idx, level_contracts in enumerate(levels):
            if not level_contracts:
                continue

            # All contracts in this level have their deps satisfied
            max_workers = min(len(level_contracts), 6)  # at most 6 ministries
            txn.audit_trail.append({
                "step": "execute", "action": "parallel_level",
                "level": level_idx, "count": len(level_contracts),
                "ministries": [c.get("ministry", "?") for c in level_contracts],
            })

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._execute_single_contract,
                        txn, contract_dict, parent_agent, results_lock,
                    ): contract_dict
                    for contract_dict in level_contracts
                }

                for future in as_completed(futures):
                    contract_dict = futures[future]
                    try:
                        future.result()
                        executed_ids.add(contract_dict["delegation_id"])
                    except Exception as e:
                        with results_lock:
                            txn.audit_trail.append({
                                "step": contract_dict.get("ministry", "?"),
                                "action": "thread_error",
                                "error": str(e),
                            })
                        executed_ids.add(contract_dict["delegation_id"])

        # Handle remaining (circular deps or skipped)
        all_ids = {c["delegation_id"] for c in txn.contracts}
        unresolved = all_ids - executed_ids
        if unresolved:
            for contract_dict in txn.contracts:
                if contract_dict["delegation_id"] in unresolved:
                    with results_lock:
                        txn.results.append({
                            "ministry": contract_dict.get("ministry", "?"),
                            "status": "skipped",
                            "reason": "unresolved dependencies",
                        })

        failed = [r for r in txn.results if r["status"] == "failed"]
        completed = [r for r in txn.results if r["status"] == "completed"]

        if failed and not completed:
            txn.state = TransactionState.ERROR.value
            txn.audit_trail.append({"step": "execute", "action": "all_failed"})
        elif failed and self.ACCEPT_PARTIAL:
            txn.state = TransactionState.EXECUTE_COMPLETE.value
            txn.audit_trail.append({
                "step": "execute", "action": "partial_success",
                "completed": len(completed), "failed": len(failed),
            })
        else:
            txn.state = TransactionState.EXECUTE_COMPLETE.value
            txn.audit_trail.append({"step": "execute", "action": "all_completed", "count": len(completed)})
        return txn

    def _build_dependency_levels(self, contracts: list) -> list:
        """Topological sort contracts into dependency levels for parallel execution.

        Returns a list of levels, where each level is a list of contract dicts
        that can execute in parallel (all their dependencies are in earlier levels).
        """
        if not contracts:
            return []

        id_to_contract = {c["delegation_id"]: c for c in contracts}
        id_to_level: Dict[str, int] = {}

        def compute_level(contract_id: str) -> int:
            if contract_id in id_to_level:
                return id_to_level[contract_id]
            contract = id_to_contract.get(contract_id)
            if not contract:
                id_to_level[contract_id] = 0
                return 0
            deps = contract.get("dependencies", [])
            if not deps:
                id_to_level[contract_id] = 0
                return 0
            max_dep_level = max(compute_level(d) for d in deps if d in id_to_contract)
            level = max_dep_level + 1
            id_to_level[contract_id] = level
            return level

        for c in contracts:
            compute_level(c["delegation_id"])

        max_level = max(id_to_level.values()) if id_to_level else 0
        levels = [[] for _ in range(max_level + 1)]
        for c in contracts:
            lvl = id_to_level[c["delegation_id"]]
            levels[lvl].append(c)

        return levels

    def _execute_single_contract(self, txn, contract_dict, parent_agent, results_lock=None):
        """Execute a single contract with retry. Thread-safe via results_lock."""
        contract = DelegationContract(**contract_dict)
        role = contract.ministry

        if not self._store.acquire_task_lock(role, contract.delegation_id):
            if results_lock:
                with results_lock:
                    txn.results.append({"ministry": role, "status": "skipped", "reason": "agent busy"})
            else:
                txn.results.append({"ministry": role, "status": "skipped", "reason": "agent busy"})
            return

        attempt = 0
        try:
            while attempt <= self.MAX_RETRIES:
                try:
                    result = self._manager.activate_agent(AgentRole(role), contract, parent_agent)
                    if results_lock:
                        with results_lock:
                            txn.results.append({"ministry": role, "status": "completed", "result": result})
                    else:
                        txn.results.append({"ministry": role, "status": "completed", "result": result})
                    break
                except Exception as e:
                    attempt += 1
                    if attempt > self.MAX_RETRIES:
                        if results_lock:
                            with results_lock:
                                txn.results.append({
                                    "ministry": role, "status": "failed",
                                    "error": str(e), "attempts": attempt,
                                })
                        else:
                            txn.results.append({
                                "ministry": role, "status": "failed",
                                "error": str(e), "attempts": attempt,
                            })
                    else:
                        if results_lock:
                            with results_lock:
                                txn.audit_trail.append({
                                    "step": role, "action": "retry",
                                    "attempt": attempt, "error": str(e),
                                })
                        else:
                            txn.audit_trail.append({
                                "step": role, "action": "retry",
                                "attempt": attempt, "error": str(e),
                            })
        finally:
            self._store.release_task_lock(role, contract.delegation_id)

    # ============================================================
    # STEP 8: Verify (刑部 — 验证循环)
    # ============================================================

    def _step_verify(self, txn, parent_agent) -> GovernanceTransaction:
        """
        刑部验证：检查执行结果是否满足 success_criteria。
        失败则标记需要修复，最多重试 MAX_VERIFY_RETRIES 次。
        类似 superpowers 的 verification-before-completion。
        """
        txn.state = TransactionState.VERIFY.value

        # Build verification summary
        results_summary = []
        for r in txn.results:
            if r["status"] == "completed":
                results_summary.append({
                    "ministry": r.get("ministry"),
                    "summary": r.get("result", {}).get("summary", "")[:500],
                })

        contract = DelegationContract(
            delegation_id=f"verify_{txn.transaction_id}",
            task=(
                "你是一个验证专家。检查执行结果是否满足成功标准。\n\n"
                f"原始需求：{txn.goal}\n"
                f"成功标准：{json.dumps(txn.sub_tasks, ensure_ascii=False)}\n"
                f"执行结果：{json.dumps(results_summary, ensure_ascii=False)}\n\n"
                "验证步骤：\n"
                "1. 逐条检查每个子任务的 success_criteria\n"
                "2. 检查是否有遗漏或不完整\n"
                "3. 检查是否有明显的错误或风险\n\n"
                '输出 JSON：{"passed": true/false, "checks": [\n'
                '  {"task_id": "t1", "passed": true/false, "detail": "..."}\n'
                '], "issues": ["..."], "fix_suggestions": ["..."]}'
            ),
            success_criteria=["输出包含 passed 布尔值的 JSON"],
            context_scope={"files": [], "memory_pointers": []},
            authority=["read"],
            deadline=_deadline(minutes=5),
            result_format={"type": "json"},
            ministry="xingbu",
            priority=txn.priority,
        )
        result = self._manager.activate_agent(AgentRole.XINGBU, contract, parent_agent)

        verify = self._parse_json_result(result.get("summary", ""))
        txn.verify_result = verify

        if verify.get("passed", False):
            txn.state = TransactionState.VERIFY_COMPLETE.value
            txn.audit_trail.append({"step": "xingbu", "action": "verify_passed"})
        else:
            # Record verification failure
            issues = verify.get("issues", [])
            txn.audit_trail.append({
                "step": "xingbu", "action": "verify_failed",
                "issues": issues,
                "fix_suggestions": verify.get("fix_suggestions", []),
            })

            # Check if we should retry execution
            verify_attempts = sum(
                1 for a in txn.audit_trail
                if a.get("step") == "xingbu" and a.get("action") == "verify_failed"
            )
            if verify_attempts <= self.MAX_VERIFY_RETRIES:
                # Re-execute failed tasks
                failed_tasks = [
                    c for c in txn.sub_tasks
                    if not verify.get("passed", False)
                ]
                txn.audit_trail.append({
                    "step": "verify", "action": "retry_execution",
                    "attempt": verify_attempts,
                })
                # Mark for re-execution by going back to EXECUTE
                txn.state = TransactionState.DISPATCH_COMPLETE.value
            else:
                # Max retries exceeded, proceed with partial results
                txn.audit_trail.append({
                    "step": "verify", "action": "max_retries_exceeded",
                    "proceeding_with_partial": True,
                })
                txn.state = TransactionState.VERIFY_COMPLETE.value

        return txn

    # ============================================================
    # STEP 9: Integrate (尚书省 — 整合结果)
    # ============================================================

    def _step_integrate(self, txn, parent_agent) -> GovernanceTransaction:
        """尚书省: integrate results with mechanical rule validation."""
        parts = []
        total_checked = 0
        total_passed = 0

        for r in txn.results:
            ministry = r.get("ministry", "?")
            status = r.get("status", "?")
            result = r.get("result", {})

            # Mechanical validation — check full output, not just summary
            try:
                role = AgentRole(ministry) if ministry != "?" else None
                if role and result:
                    violations = self._validator.validate_agent_output(role, result)
                    total_checked += 1
                    if violations:
                        for v in violations:
                            self._feedback.record_violation(
                                txn.transaction_id, ministry, "auto", v,
                            )
                        txn.audit_trail.append({
                            "step": "integrate", "action": "rule_violations",
                            "role": ministry, "violations": violations,
                        })
                        # Log but don't block — violations are recorded for analysis
                    else:
                        total_passed += 1
                        self._feedback.record_compliance(
                            txn.transaction_id, ministry, 1, 1,
                        )
            except (ValueError, Exception):
                pass  # Don't let validation errors break integration

            # Legacy boundary check (kept for backward compat)
            if ministry == "bingbu" and self._violates_bingbu_boundary(r):
                txn.audit_trail.append({
                    "step": "integrate", "action": "boundary_violation",
                    "ministry": "bingbu", "detail": "输出包含越界内容，已过滤",
                })
                continue

            summary = result.get("summary", r.get("error", "no output"))
            parts.append(f"### {ministry} ({status})\n{summary}")

        # Add verification summary
        if txn.verify_result:
            verify_status = "PASSED" if txn.verify_result.get("passed") else "FAILED"
            parts.append(f"### 验证结果 ({verify_status})\n{json.dumps(txn.verify_result, ensure_ascii=False)}")

        txn.integrated_result = "\n\n".join(parts) if parts else "无结果"
        txn.state = TransactionState.COMPLETE.value

        # Record to structured memory
        self._store.append_decision(txn)
        self._update_boulder_state(txn)

        txn.audit_trail.append({
            "step": "integrate", "action": "complete",
            "validation": {"checked": total_checked, "passed": total_passed},
        })
        return txn

    def _update_boulder_state(self, txn: GovernanceTransaction):
        """Update Boulder State with completed transaction."""
        boulder = self._store.load_boulder_state()
        goal_entry = {
            "txn_id": txn.transaction_id,
            "goal": txn.goal[:200],
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # Remove from active if present
        boulder.active_goals = [
            g for g in boulder.active_goals if g.get("txn_id") != txn.transaction_id
        ]
        boulder.completed_goals.append(goal_entry)
        # Keep last 50 completed
        if len(boulder.completed_goals) > 50:
            boulder.completed_goals = boulder.completed_goals[-50:]
        self._store.save_boulder_state(boulder)

    def _violates_bingbu_boundary(self, result: dict) -> bool:
        summary = result.get("result", {}).get("summary", "")
        violation_markers = [
            "COMPLETE", "REJECTED", "APPROVED",
            "状态已更新", "任务完成", "最终结果",
        ]
        return any(marker in summary for marker in violation_markers)

    def _step_error(self, txn, parent_agent) -> GovernanceTransaction:
        txn.state = TransactionState.ERROR.value
        return txn

    # ============================================================
    # Parsing helpers
    # ============================================================

    @staticmethod
    def _parse_json_result(summary: str) -> Dict[str, Any]:
        """Extract JSON from agent summary."""
        try:
            if "{" in summary:
                start = summary.index("{")
                depth = 0
                for i, ch in enumerate(summary[start:], start):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            return json.loads(summary[start:i + 1])
        except (json.JSONDecodeError, ValueError):
            pass
        return {}

    @staticmethod
    def _parse_verdict(summary: str) -> Dict[str, Any]:
        """Parse 门下省 verdict from agent summary."""
        # Try JSON first
        try:
            if "{" in summary:
                start = summary.index("{")
                depth = 0
                for i, ch in enumerate(summary[start:], start):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            data = json.loads(summary[start:i + 1])
                            if "verdict" in data:
                                return data
        except (json.JSONDecodeError, ValueError):
            pass

        # Keyword fallback
        lower = summary.lower()
        if "reject" in lower or "驳回" in lower or "拒绝" in lower:
            return {"verdict": "reject", "notes": summary[:300]}
        if "revise" in lower or "修改" in lower or "打回" in lower:
            return {"verdict": "revise", "notes": summary[:300]}
        return {"verdict": "approve", "notes": summary[:300]}
