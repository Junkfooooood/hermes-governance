# Handshake Protocol

## Purpose

The handshake is the interaction between 尚书省 and a 六部 agent when dispatching a task. Since agents are **resident roles** (not spawned per task), the handshake activates an idle agent and establishes the task contract.

## Protocol Flow

```
1. 尚书省 prepares delegation contract
2. 尚书省 sends DISPATCH to target 六部 agent
3. Agent transitions from IDLE → ACTIVATED
4. Agent loads task context and delegation contract
5. Agent responds with ACK (confirmed) or QUERY (needs clarification)
6. 尚书省 confirms ACK or answers QUERY
7. Agent enters EXECUTE stage
```

## Handshake Messages

### 1. 尚书省 → 六部: DISPATCH

```yaml
---
message_id: msg_<uuid>
from: shangshu
to: <ministry_agent_id>
intent: DISPATCH
priority: normal
timestamp: <ISO8601>
trace_id: <uuid>
---
delegation:
  delegation_id: del_<timestamp>_<seq>
  task: <specific task description>
  success_criteria:
    - <verifiable condition 1>
    - <verifiable condition 2>
  context_scope:
    - <file or doc path>
  authority:
    - <permission level>
  deadline: <ISO8601>
  result_format:
    type: text | json | file
    schema: <expected structure>
  max_iterations: 3
  priority: normal
  ministry: <target ministry>
  token_budget: <optional token limit>
```

### 2. 六部 → 尚书省: ACK (Confirmed)

```yaml
---
message_id: msg_<uuid>
from: <ministry_agent_id>
to: shangshu
intent: ACK
priority: normal
timestamp: <ISO8601>
trace_id: <uuid>
---
ack:
  delegation_id: del_<id>
  status: CONFIRMED
  agent_id: <ministry_agent_id>
  role: <ministry role>
  capabilities:
    tools: [<available tools>]
    domain: <declared domain>
  current_load: busy
```

### 3. 六部 → 尚书省: QUERY (Needs Clarification)

```yaml
---
message_id: msg_<uuid>
from: <ministry_agent_id>
to: shangshu
intent: QUERY
priority: normal
timestamp: <ISO8601>
trace_id: <uuid>
---
query:
  delegation_id: del_<id>
  status: NEEDS_CLARIFICATION
  questions:
    - field: <which part of the contract is unclear>
      issue: <what is unclear>
      suggested_resolution: <what the agent thinks, if any>
```

## Handshake Rules

1. Agent must respond within 30 seconds of receiving DISPATCH.
2. If clarification is needed, 尚书省 must respond within 60 seconds.
3. Agent must NOT begin execution before ACK is confirmed.
4. If agent cannot execute (missing tools, insufficient authority), it must report in ACK with `status: REJECTED` and reason.
5. Handshake is logged as part of the audit trail.
6. Only 尚书省 can initiate handshakes — 六部 cannot handshake with each other.
