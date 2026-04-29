# Agent Lifecycle Rules

## 1. Lifecycle Stages

```
 ┌─────────┐
 │  SPAWN  │  ← Coordinator initiates
 └────┬────┘
      ▼
 ┌─────────────┐
 │  HANDSHAKE  │  ← Advertise capabilities, receive role
 └────┬────────┘
      ▼
 ┌─────────────┐
 │   EXECUTE   │  ← Main task loop (Ralph Loop)
 └────┬────────┘
      ▼
 ┌─────────────┐
 │   REPORT    │  ← Return results to coordinator
 └────┬────────┘
      ▼
 ┌─────────────┐
 │   REVIEW    │  ← Reviewer evaluates output
 └────┬────────┘
      ▼
 ┌─────────────┐
 │   RETIRE    │  ← Clean up context, record feedback
 └─────────────┘
```

## 2. Stage Entry & Exit Criteria

### SPAWN
- **Entry**: Coordinator issues a delegation contract
- **Exit**: Agent process created, session_id assigned, role loaded
- **Max time**: 10 seconds

### HANDSHAKE
- **Entry**: Agent loads AGENTS.md + role definition + constitution
- **Exit**: ACK sent to coordinator with capabilities + confirmed understanding
- **Required**: Agent must parse and confirm the delegation contract
- **Max time**: 30 seconds

### EXECUTE
- **Entry**: Handshake complete, task scope loaded
- **Exit**: Result produced OR blocker identified OR deadline exceeded
- **Max iterations**: 3 Ralph Loop cycles per task
- **Checkpoint**: After each turn, verify progress against success criteria

### REPORT
- **Entry**: Execution complete, self-review passed
- **Exit**: RESULT message sent to coordinator in specified format
- **Required**: Include all fields from delegation contract's result_format
- **Max time**: 60 seconds to format and send

### REVIEW
- **Entry**: Coordinator sends task + output to reviewer
- **Exit**: Reviewer returns APPROVE / REVISE / REJECT verdict
- **Max time**: 120 seconds
- **Constraint**: Reviewer must NOT see executor reasoning (PGE pattern)

### RETIRE
- **Entry**: Review complete, coordinator has accepted final output
- **Exit**: Session cleaned up, hooks fired, feedback recorded
- **Required**:
  - `on_session_end` hooks fired
  - Working memory discarded (or summarized if valuable)
  - Feedback recorded for consequential decisions
  - Session state written to session store
- **Max time**: 30 seconds

## 3. Session Limits

All agent sessions have hard limits (from config):
- `max_turns: 150` — total API call iterations
- `gateway_timeout: 1800` — maximum session lifetime in seconds
- `max_iterations: 3` — Ralph Loop cycles per task

When a limit is reached:
1. Agent sends partial results (if any) to coordinator
2. Agent enters RETIRE stage immediately
3. Coordinator decides whether to re-delegate or accept partial results

## 4. Cleanup Requirements

Before retiring, every agent must:
- [ ] Discard working memory (unless summarized for short-term promotion)
- [ ] Close open file handles, database connections, network sockets
- [ ] Flush pending log entries
- [ ] Record feedback for consequential actions (feedback loop)
- [ ] Report final session metrics to coordinator (turns used, tools called, errors)

## 5. Re-spawn

A retired agent may be re-spawned by the coordinator for a new task. Re-spawned agents:
- Start with clean context (no carryover from previous session)
- Load fresh harness rules (rules may have been updated)
- Receive a new session_id
- Do NOT inherit previous session's working or short-term memory

## 6. Orphaned Agents

If the coordinator session ends before child agents:
- Child agents receive `SESSION_END` signal
- Child agents enter RETIRE immediately
- Child agents report partial results to session store (not to coordinator directly)
- Orphaned results are available for retrieval but not automatically aggregated
