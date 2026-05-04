# Communication Rules

## 1. Communication Model

All inter-agent communication is:
- **Structured** — follows a standard message format
- **Traceable** — every message has an ID and trace context
- **Radial** — all flows through 尚书省, no lateral communication between 六部
- **Asynchronous** — messages are queued, not real-time

## 2. Radial Communication Architecture

```
        祖 Agent
           ↓
      三省 (中书省 → 门下省 → 尚书省)
           ↓
        尚书省
       ↙  ↓  ↘
    工部  户部  兵部
    礼部  刑部  吏部
```

### Core Rules

1. **六部之间禁止横向通信** — 不直接传任务、不直接交换意见、不直接要求对方改动
2. **所有跨部协调由尚书省统一处理**
3. **六部只与尚书省通信** — 接受派发、回报结果
4. **三省之间单向流转** — 中书省 → 门下省 → 尚书省

### Why Radial

| Problem | Lateral Communication | Radial (via 尚书省) |
|---------|----------------------|-------------------|
| Accountability | Unclear who's responsible | Single chain |
| Negotiation | "You go first" loops | 尚书省 decides |
| Process control | Tasks deform | 尚书省 maintains integrity |
| Auditability | Hard to trace | Single path |

## 3. Standard Message Format

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

## 4. Intent Types

| Intent | Direction | Purpose |
|--------|-----------|---------|
| `DELEGATE` | 尚书省 → 六部 | Issue a task delegation |
| `REPORT` | 六部 → 尚书省 | Return task results |
| `PLAN` | 中书省 → 门下省 | Submit plan for review |
| `VERDICT` | 门下省 → 中书省/尚书省 | Approve/Reject plan |
| `DISPATCH` | 尚书省 → 六部 | Dispatch sub-tasks |
| `INTEGRATE` | 尚书省 → 祖 Agent | Submit integrated result |
| `QUERY` | Any → parent | Request information |
| `RESPONSE` | parent → Any | Reply to a QUERY |
| `ALERT` | Any → 尚书省 | Raise a blocking issue |
| `ACK` | Any → Any | Confirm receipt |
| `HEARTBEAT` | 六部 → 尚书省 | Periodic liveness signal |

## 5. Priority Levels

| Priority | Use When | Expected Response |
|----------|----------|-------------------|
| `low` | Informational, no action needed | Best effort |
| `normal` | Standard task communication | Within current turn |
| `high` | Blocking issue, deadline approaching | Before next turn |
| `critical` | Safety issue, system failure | Immediate |

## 6. Audit Trail

All messages are logged with:
- `message_id`, `trace_id`, `from`, `to`, `intent`, `timestamp`
- Content hash (for integrity verification)
- Acknowledgment timestamp

Logs are written to session storage and are queryable for traceability (Constitution Law 4).

## 7. Communication Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| 六部 direct lateral communication | Breaks radial structure | Always go through 尚书省 |
| Sending unstructured text | No parseable metadata | Always use standard message format |
| "Hey can you..." without intent | Receiver can't prioritize | Include explicit intent |
| Assuming understanding | No confirmation | Receiver must ACK |
| Silent failure | No one knows it broke | Failed messages must generate ALERT |
