# Communication Rules

## 1. Communication Model

All inter-agent communication is:
- **Structured** — follows a standard message format
- **Traceable** — every message has an ID and trace context
- **Point-to-point or broadcast** — no anonymous channels
- **Asynchronous** — messages are queued, not real-time

## 2. Standard Message Format

Every inter-agent message must conform to the message spec ([`protocols/message-spec.md`](../protocols/message-spec.md)).

Minimal valid message:
```yaml
---
message_id: msg_<uuid>
from: agent_<id>
to: agent_<id>
intent: DELEGATE
timestamp: <ISO8601>
trace_id: <uuid>
---
<content>
```

## 3. Intent Types

| Intent | Direction | Purpose |
|--------|-----------|---------|
| `DELEGATE` | Coordinator → Executor | Issue a task delegation contract |
| `REPORT` | Executor → Coordinator | Return task results |
| `REVIEW` | Coordinator → Reviewer | Request independent output review |
| `VERDICT` | Reviewer → Coordinator | Return review decision |
| `QUERY` | Any → Any | Request information |
| `RESPONSE` | Any → Any | Reply to a QUERY |
| `ALERT` | Any → Coordinator | Raise a blocking issue or safety flag |
| `ACK` | Any → Any | Confirm receipt and understanding |
| `HEARTBEAT` | Any → Coordinator | Periodic liveness signal |

## 4. Priority Levels

| Priority | Use When | Expected Response |
|----------|----------|-------------------|
| `low` | Informational, no action needed | Best effort |
| `normal` | Standard task communication | Within current turn |
| `high` | Blocking issue, deadline approaching | Before next turn |
| `critical` | Safety issue, system failure | Immediate. Bypasses normal queues. |

Only `ALERT` intents may carry `critical` priority.

## 5. Message Routing

```
Executor A ──REPORT──→ Coordinator
Executor B ──REPORT──→ Coordinator
Reviewer   ──VERDICT─→ Coordinator
Coordinator ──DELEGATE─→ Executor A
Coordinator ──REVIEW──→ Reviewer
Any agent  ──ALERT──→ Coordinator (always routed, never queued)
```

Peer-to-peer messages (QUERY/RESPONSE) are allowed but must CC the coordinator for traceability.

## 6. Audit Trail

All messages are logged with:
- `message_id`, `trace_id`, `from`, `to`, `intent`, `timestamp`
- Content hash (for integrity verification)
- Acknowledgment timestamp (when the receiver confirmed)

Logs are written to session storage and are queryable for traceability (Law 4).

## 7. Communication Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| Sending unstructured text | No parseable metadata | Always use standard message format |
| "Hey can you..." without intent | Receiver can't prioritize | Include explicit intent |
| Long-running chat threads | Context bloat, hidden state | Each exchange is a discrete message pair |
| Assuming understanding | No confirmation | Receiver must ACK |
| Silent failure | No one knows it broke | Failed messages must generate ALERT |
