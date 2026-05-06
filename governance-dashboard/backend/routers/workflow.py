"""GET /api/workflow — governance workflow stages with active agents."""

from fastapi import APIRouter

router = APIRouter()

_bridge = None


def init(bridge):
    global _bridge
    _bridge = bridge


# Canonical workflow stages
STAGES = [
    {"id": "interview", "label": "需求澄清", "agent_role": "zhongshu", "description": "中书省通过提问澄清需求"},
    {"id": "plan", "label": "制定方案", "agent_role": "zhongshu", "description": "中书省制定执行方案"},
    {"id": "review_spec", "label": "合规审核", "agent_role": "menxia", "description": "门下省审核方案合规性"},
    {"id": "review_quality", "label": "质量审核", "agent_role": "menxia", "description": "门下省审核方案质量"},
    {"id": "decompose", "label": "任务分解", "agent_role": "shangshu", "description": "尚书省拆解为原子任务"},
    {"id": "dispatch", "label": "任务派发", "agent_role": "shangshu", "description": "尚书省向六部派发合同"},
    {"id": "execute", "label": "并行执行", "agent_role": "六部", "description": "六部并行执行原子任务"},
    {"id": "verify", "label": "结果验证", "agent_role": "xingbu", "description": "刑部验证执行结果"},
    {"id": "integrate", "label": "结果整合", "agent_role": "shangshu", "description": "尚书省整合最终结果"},
]

# Map transaction state → workflow stage
STATE_TO_STAGE = {
    "created": "interview",
    "interview": "interview",
    "interview_complete": "interview",
    "plan": "plan",
    "plan_complete": "plan",
    "review": "review_spec",
    "review_spec_complete": "review_spec",
    "review_quality": "review_quality",
    "review_quality_complete": "review_quality",
    "decompose": "decompose",
    "decompose_complete": "decompose",
    "dispatch": "dispatch",
    "dispatch_complete": "dispatch",
    "execute": "execute",
    "execute_complete": "execute",
    "verify": "verify",
    "verify_complete": "verify",
    "integrate": "integrate",
    "complete": "integrate",
}

TERMINAL_STATES = {"complete", "rejected", "error"}


@router.get("/api/workflow/stages")
async def get_workflow_stages():
    """Return workflow stages with current activity."""
    all_txns = _bridge.load_all_transactions()
    all_agents = _bridge.load_all_agents()

    # Build agent lookup
    agent_map = {a.get("role", ""): a for a in all_agents}

    # For each stage, find which transactions and agents are active there
    enriched_stages = []
    for stage in STAGES:
        stage_id = stage["id"]
        active_txns = []
        idle_txns = []

        for txn in all_txns:
            txn_state = txn.get("state", "")
            txn_stage = STATE_TO_STAGE.get(txn_state, "")
            is_terminal = txn_state in TERMINAL_STATES

            if txn_stage == stage_id:
                entry = {
                    "txn_id": txn.get("txn_id", ""),
                    "goal": txn.get("goal", "")[:80],
                    "state": txn_state,
                    "sub_task_count": len(txn.get("sub_tasks", [])),
                }
                if is_terminal:
                    idle_txns.append(entry)
                else:
                    active_txns.append(entry)

        # Find which agents are active in this stage
        stage_role = stage["agent_role"]
        active_agents = []

        if stage_role == "六部":
            # All department agents
            for role, agent in agent_map.items():
                if agent.get("tier") == "department":
                    lifecycle = agent.get("lifecycle", "idle")
                    if lifecycle in ("execute", "activated"):
                        active_agents.append({
                            "role": role,
                            "lifecycle": lifecycle,
                            "active_contract": agent.get("active_contract_id"),
                        })
        else:
            agent = agent_map.get(stage_role)
            if agent:
                lifecycle = agent.get("lifecycle", "idle")
                if lifecycle in ("execute", "activated"):
                    active_agents.append({
                        "role": stage_role,
                        "lifecycle": lifecycle,
                        "active_contract": agent.get("active_contract_id"),
                    })

        enriched_stages.append({
            **stage,
            "active_transactions": active_txns,
            "completed_transactions": idle_txns,
            "active_agents": active_agents,
            "is_active": len(active_txns) > 0,
        })

    return {"stages": enriched_stages}


@router.get("/api/workflow/overview")
async def get_workflow_overview():
    """Quick summary: how many txns in each stage."""
    all_txns = _bridge.load_all_transactions()
    stage_counts = {s["id"]: 0 for s in STAGES}
    stage_counts["terminal"] = 0

    for txn in all_txns:
        txn_state = txn.get("state", "")
        stage = STATE_TO_STAGE.get(txn_state, "terminal")
        if txn_state in TERMINAL_STATES:
            stage_counts["terminal"] = stage_counts.get("terminal", 0) + 1
        else:
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

    return {"stage_counts": stage_counts, "total": len(all_txns)}
