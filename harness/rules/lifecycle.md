# Agent Lifecycle Rules

## 1. Resident Role Lifecycle

三省六部 are **resident roles** — permanent, not spawned/retired per task.

```
┌──────────────┐
│    IDLE      │  ← Waiting for task assignment
└──────┬───────┘
       ▼
┌──────────────┐
│  ACTIVATED   │  ← 尚书省 dispatches task
└──────┬───────┘
       ▼
┌──────────────┐
│   EXECUTE    │  ← Perform domain work
└──────┬───────┘
       ▼
┌──────────────┐
│   REPORT     │  ← Return results to 尚书省
└──────┬───────┘
       ▼
┌──────────────┐
│  DEACTIVATE  │  ← Return to IDLE, retain memory
└──────────────┘
```

No RETIRE step — agents persist and accumulate experience across tasks.

## 2. Stage Details

### IDLE
- Agent is resident, holding persistent context and memory
- Waiting for 尚书省 to dispatch a task
- Can receive HEARTBEAT pings

### ACTIVATED
- **Entry**: 尚书省 sends DISPATCH with delegation contract
- **Exit**: Agent ACKs with capabilities and confirmed understanding
- **Max time**: 30 seconds

### EXECUTE
- **Entry**: Activation complete, task scope loaded
- **Exit**: Result produced OR blocker identified OR deadline exceeded
- **Max iterations**: 3 per task
- **Checkpoint**: After each turn, verify progress against success criteria

### REPORT
- **Entry**: Execution complete
- **Exit**: RESULT message sent to 尚书省
- **Max time**: 60 seconds

### DEACTIVATE
- **Entry**: Report sent, 尚书省 has accepted result
- **Exit**: Return to IDLE
- **Required**:
  - Record feedback for consequential decisions
  - Update agent memory with task learnings
  - Release temporary resources
  - Report session metrics to 吏部 (turns used, tools called, tokens consumed)

## 3. Task Session Limits

Each task session has hard limits:
- `max_turns: 150` — total API call iterations
- `gateway_timeout: 1800` — maximum session lifetime in seconds
- `max_iterations: 3` — execution cycles per task

When a limit is reached:
1. Agent sends partial results to 尚书省
2. Agent enters DEACTIVATE immediately
3. 尚书省 decides whether to re-dispatch or accept partial results

## 4. Token Budget Enforcement

吏部 monitors token consumption per task session:
- Real-time metering of every API call
- Alert when consumption exceeds 80% of budget (from 尚书省)
- Hard stop at 120% — agent must report and deactivate
- Repeated retries trigger alert to 尚书省

## 5. Orphaned Tasks

If 尚书省 session ends before 六部 complete:
- 六部 receive SESSION_END signal
- 六部 enter DEACTIVATE immediately
- Partial results written to session store
- Orphaned results available for retrieval but not automatically aggregated
