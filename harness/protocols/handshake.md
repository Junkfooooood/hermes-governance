# Handshake Protocol

## Purpose

The handshake is the first interaction between a newly spawned agent and the coordinator. It establishes identity, capabilities, and the task contract.

## Protocol Flow

```
1. Coordinator spawns agent → sends DELEGATE message with contract
2. Agent loads harness (AGENTS.md → role → constitution)
3. Agent parses delegation contract
4. Agent responds with ACK (confirmed) or QUERY (needs clarification)
5. Coordinator confirms ACK or answers QUERY
6. Agent enters EXECUTE stage
```

## Handshake Messages

### 1. Coordinator → Agent: DELEGATE

```yaml
---
message_id: msg_<uuid>
from: coordinator_<id>
to: agent_<id>
intent: DELEGATE
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
```

### 2. Agent → Coordinator: ACK (Confirmed)

```yaml
---
message_id: msg_<uuid>
from: agent_<id>
to: coordinator_<id>
intent: ACK
priority: normal
timestamp: <ISO8601>
trace_id: <uuid>
---
ack:
  delegation_id: del_<id>
  status: CONFIRMED
  agent_id: agent_<id>
  role: executor
  capabilities:
    tools: [<available tools>]
    domain: <if specialist>
  current_load: busy
  session_id: sess_<id>
```

### 3. Agent → Coordinator: QUERY (Needs Clarification)

```yaml
---
message_id: msg_<uuid>
from: agent_<id>
to: coordinator_<id>
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

1. Agent must respond within 30 seconds of receiving DELEGATE.
2. If clarification is needed, coordinator must respond within 60 seconds.
3. Agent must NOT begin execution before ACK is confirmed.
4. If agent cannot execute (missing tools, insufficient authority), it must report in ACK with `status: REJECTED` and reason.
5. Handshake is logged as part of the audit trail.
