# Standard Message Specification

## Purpose

All inter-agent communication in the Hermes ecosystem uses this message format. It is designed for:
- **Machine readability**: structured YAML frontmatter for tooling
- **Agent readability**: clear natural-language content body
- **Traceability**: every message carries full provenance

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

| Intent | Meaning | Expected Response |
|--------|---------|-------------------|
| `DELEGATE` | Task assignment with contract | `ACK` or `QUERY` |
| `REPORT` | Task result delivery | `ACK` |
| `REVIEW` | Request for independent review | `VERDICT` |
| `VERDICT` | Review decision | `ACK` |
| `QUERY` | Request for information | `RESPONSE` |
| `RESPONSE` | Answer to a query | `ACK` |
| `ALERT` | Safety or blocking issue | `ACK` (immediate) |
| `ACK` | Confirmation of receipt + understanding | None (terminal) |
| `HEARTBEAT` | Liveness signal | None (informational) |

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

### For REPORT
Content body contains the task result in the format specified by the delegation contract's `result_format`.

### For VERDICT
Content body contains a review report (see [`roles/reviewer.md`](../roles/reviewer.md)).

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

## Message Integrity

- `content_hash`: SHA-256 of the content body (for detecting tampering or corruption).
- Optional but recommended for messages that contain task results or review verdicts.
- When `content_hash` is present, the receiver should verify before processing.

## Message Sequencing

- Messages within a trace (same `trace_id`) are ordered by `timestamp`.
- Receivers process messages in timestamp order.
- If timestamps are equal, `message_id` lexicographic order breaks ties.
