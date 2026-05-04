# Standard Message Specification

## Purpose

All inter-agent communication in the Hermes ecosystem uses this message format. It is designed for:
- **Machine readability**: structured YAML frontmatter for tooling
- **Agent readability**: clear natural-language content body
- **Traceability**: every message carries full provenance
- **Radial compliance**: all messages follow the radial communication structure

## Message Schema

```yaml
---
message_id: msg_<uuid>           # Required. Globally unique.
from: <agent_id>                  # Required. Sender's agent_id.
to: <agent_id> | broadcast       # Required. Recipient or "broadcast".
intent: <intent_type>            # Required. One of the defined intent types.
priority: <priority_level>       # Required. low | normal | high | critical.
timestamp: <ISO8601>             # Required. When the message was created.
trace_id: <uuid>                 # Required. Root trace for the entire session.
in_reply_to: <message_id>        # Optional. For response messages.
content_hash: <sha256>           # Optional. For integrity verification.
---
<content body — natural language or structured data>
```

## Intent Types

| Intent | Direction | Purpose | Expected Response |
|--------|-----------|---------|-------------------|
| `DELEGATE` | 祖 Agent → 三省 | Issue a top-level task | `ACK` or `QUERY` |
| `PLAN` | 中书省 → 门下省 | Submit plan for review | `VERDICT` |
| `VERDICT` | 门下省 → 中书省/尚书省 | Approve or reject plan | `ACK` |
| `DISPATCH` | 尚书省 → 六部 | Dispatch sub-task | `ACK` or `QUERY` |
| `REPORT` | 六部 → 尚书省 | Return task results | `ACK` |
| `INTEGRATE` | 尚书省 → 祖 Agent | Submit integrated result | `ACK` |
| `QUERY` | Any → parent | Request information | `RESPONSE` |
| `RESPONSE` | parent → Any | Answer to a query | `ACK` |
| `ALERT` | Any → 尚书省 | Safety or blocking issue | `ACK` (immediate) |
| `ACK` | Any → Any | Confirmation of receipt | None (terminal) |
| `HEARTBEAT` | 六部 → 尚书省 | Liveness signal | None (informational) |

## Priority Levels

| Priority | Latency Expectation | Use Case |
|----------|---------------------|----------|
| `critical` | Immediate. Bypasses queues. | Safety alerts only |
| `high` | Within current turn | Blocking issue, deadline approaching |
| `normal` | Within 2 turns | Standard task communication |
| `low` | Best effort | Informational, no action needed |

Only `ALERT` intents may use `critical` priority.

## Content Body Formats

### For DELEGATE
Content body contains a delegation contract (see [`delegation-spec.md`](delegation-spec.md)).

### For PLAN
Content body contains the hypothesis and validation action schema from 中书省.

### For VERDICT
Content body contains the review decision from 门下省:
- `APPROVED` — plan is sound, proceed to dispatch
- `REJECTED` — plan has issues, return to 中书省 with reasons
- Max 3 rounds of review before escalation to 祖 Agent

### For DISPATCH
Content body contains a sub-task delegation contract for a specific 六部.

### For REPORT
Content body contains the task result in the format specified by the delegation contract's `result_format`.

### For INTEGRATE
Content body contains the integrated result from 尚书省, combining outputs from multiple 六部.

### For QUERY / RESPONSE
Free-form natural language, but must include:
- What is being asked/answered
- Why it matters in context
- Any assumptions

### For ALERT
Must include:
- What triggered the alert
- Which agent/tool/session is affected
- Severity assessment
- Recommended action

## Routing Rules

| From | To | Allowed |
|------|----|---------|
| 祖 Agent | 三省 | Yes |
| 中书省 | 门下省 | Yes |
| 门下省 | 中书省 / 尚书省 | Yes |
| 尚书省 | 六部 | Yes |
| 六部 | 尚书省 | Yes |
| 尚书省 | 祖 Agent | Yes |
| 六部 | 六部 | **NO** — must route through 尚书省 |
| 六部 | 祖 Agent | **NO** — must route through 尚书省 |

## Message Integrity

- `content_hash`: SHA-256 of the content body (for detecting tampering or corruption).
- Optional but recommended for messages that contain task results or review verdicts.
- When `content_hash` is present, the receiver should verify before processing.

## Message Sequencing

- Messages within a trace (same `trace_id`) are ordered by `timestamp`.
- Receivers process messages in timestamp order.
- If timestamps are equal, `message_id` lexicographic order breaks ties.
