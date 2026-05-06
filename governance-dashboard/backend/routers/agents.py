"""GET /api/agents — agent list and detail with task context."""

from fastapi import APIRouter, HTTPException

router = APIRouter()

_bridge = None
_task_index = None


def init(bridge, task_index=None):
    global _bridge, _task_index
    _bridge = bridge
    _task_index = task_index


@router.get("/api/agents")
async def list_agents():
    agents = _bridge.load_all_agents()
    # Enrich each agent with task context
    enriched = []
    for agent in agents:
        enriched.append(_enrich_agent(agent))
    return {"agents": enriched}


@router.get("/api/agents/{role}")
async def get_agent(role: str):
    agent = _bridge.load_agent_state(role)
    if not agent:
        raise HTTPException(
            status_code=404,
            detail={"code": "AGENT_NOT_FOUND", "message": f"Agent {role} not found"},
        )
    return _enrich_agent(agent)


def _enrich_agent(agent: dict) -> dict:
    """Add task context to agent data by scanning transaction files."""
    role = agent.get("role", "")
    completed_contracts = agent.get("completed_contracts", [])
    active_contract_id = agent.get("active_contract_id")

    # Scan all transactions to find where this agent participated
    tasks_involved = []
    all_txns = _bridge.load_all_transactions()

    for txn in all_txns:
        txn_id = txn.get("txn_id", "")
        sub_tasks = txn.get("sub_tasks", [])
        contracts = txn.get("contracts", [])
        results = txn.get("results", [])
        audit_trail = txn.get("audit_trail", [])

        # Find contracts assigned to this agent's role
        agent_contracts = [
            c for c in contracts if c.get("ministry") == role
        ]

        # Find results from this agent
        agent_results = [
            r for r in results if r.get("ministry") == role
        ]

        # Find audit entries involving this agent
        agent_audit = [
            a for a in audit_trail if a.get("step") == role
        ]

        # Check if any completed contracts belong to this txn
        txn_contract_ids = {c.get("delegation_id", "") for c in contracts}
        agent_completed_in_txn = [
            c for c in completed_contracts if c in txn_contract_ids
        ]

        if agent_contracts or agent_results or agent_audit or agent_completed_in_txn:
            # Determine agent's status in this transaction
            agent_status = _determine_agent_txn_status(
                role, txn, agent_contracts, agent_results, active_contract_id
            )

            # Find the sub-tasks this agent is handling
            agent_subtasks = []
            for st in sub_tasks:
                st_ministry = st.get("ministry", "")
                if st_ministry == role:
                    # Find corresponding result
                    st_result = None
                    for r in agent_results:
                        # Match by contract delegation_id pattern
                        st_result = r
                    agent_subtasks.append({
                        "id": st.get("id", ""),
                        "task": st.get("task", ""),
                        "status": _get_subtask_status(st, agent_results, contracts, role),
                        "success_criteria": st.get("success_criteria", []),
                    })

            tasks_involved.append({
                "txn_id": txn_id,
                "goal": txn.get("goal", "")[:100],
                "txn_state": txn.get("state", ""),
                "agent_status": agent_status,
                "sub_tasks": agent_subtasks,
                "contracts_count": len(agent_contracts),
                "results_count": len(agent_results),
            })

    agent["tasks_involved"] = tasks_involved

    # Determine current context
    active_tasks = [t for t in tasks_involved if t["agent_status"] == "active"]
    if active_tasks:
        agent["current_context"] = {
            "txn_id": active_tasks[0]["txn_id"],
            "goal": active_tasks[0]["goal"],
            "stage": active_tasks[0]["txn_state"],
        }
    else:
        agent["current_context"] = None

    return agent


def _determine_agent_txn_status(
    role: str, txn: dict, contracts: list, results: list, active_contract_id
) -> str:
    """Determine agent's status within a transaction."""
    txn_state = txn.get("state", "")

    # Check if agent has an active contract in this txn
    if active_contract_id:
        txn_contract_ids = {c.get("delegation_id", "") for c in contracts}
        if active_contract_id in txn_contract_ids:
            return "active"

    # If transaction is terminal, agent is done
    if txn_state in ("complete", "rejected", "error"):
        return "completed"

    # Check if agent has pending work
    if contracts and not results:
        return "pending"

    # Check if agent has results
    if results:
        failed = [r for r in results if r.get("status") == "failed"]
        if failed:
            return "failed"
        return "completed"

    return "idle"


def _get_subtask_status(
    subtask: dict, results: list, contracts: list, role: str
) -> str:
    """Determine status of a specific sub-task for an agent."""
    # Check if there's a result for this sub-task
    for r in results:
        if r.get("ministry") == role:
            return r.get("status", "completed")

    # Check if there's a contract (pending execution)
    for c in contracts:
        if c.get("ministry") == role:
            return "pending"

    return "waiting"
