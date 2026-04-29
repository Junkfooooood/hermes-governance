# Collaboration Rules

## 1. Agent Discovery

Agents discover each other through the coordinator. There is no peer-to-peer discovery.

### Discovery Flow
```
1. Agent spawns → loads role + capabilities
2. Agent handshakes with coordinator
3. Coordinator registers agent in active session registry
4. Coordinator informs other agents of new capability (if relevant)
```

### Capability Advertisement
Each agent advertises at handshake:
```yaml
agent_id: agent_<uuid>
role: executor | reviewer | specialist
capabilities:
  tools: [list of available tools]
  domain: [specialist only — declared domains]
  max_concurrent: 1
current_load: idle | busy
session_id: sess_<id>
```

## 2. Coordinator Authority

The coordinator is the single point of orchestration for a session.

- Coordinator assigns tasks, resolves conflicts, and aggregates results.
- No agent may delegate to another agent except the coordinator.
- No agent may spawn child agents except the coordinator.
- Coordinator decisions are final within the session scope.

### Coordinator Limits
- `max_concurrent_children: 3` (from config)
- `max_spawn_depth: 1` (from config — children cannot spawn grandchildren)
- Coordinator must not become a bottleneck — if 3 children are running, queue additional tasks.

## 3. Conflict Resolution

Priority order for resolving conflicts:
1. **Safety** — any safety flag overrides all other considerations
2. **Constitution** — immutable laws override local rules
3. **Success Criteria** — output meeting criteria beats output that doesn't
4. **Reviewer Verdict** — independent reviewer assessment breaks ties
5. **Coordinator Decision** — final arbitration within session

## 4. Shared State

Agents share state through pointers, not copies.

- Memory is read from the pointer layer (SOUL.md → memory.md → layer lookup).
- Agents do NOT copy memory into their context — they retrieve on demand.
- Write access to shared memory is governed by AMS, not by individual agents.
- Session state (working memory) is local to each agent and cleaned up on session end.

## 5. Turn-Taking

The coordinator manages turn order:

```
1. Coordinator delegates tasks to executors (parallel where independent)
2. Executors execute independently
3. Executors report results to coordinator
4. Coordinator sends results to reviewer (if configured)
5. Reviewer returns verdict
6. Coordinator aggregates and responds
```

Agents do NOT interrupt other agents mid-execution. Urgent safety flags bypass this rule — any agent may alert the coordinator immediately.

## 6. Multi-Agent Sessions

- Each agent session is isolated (separate context window).
- Agents communicate only through structured messages (see [`protocols/message-spec.md`](../protocols/message-spec.md)).
- The root coordinator session is the only session that communicates directly with the human user.
- Sub-agent sessions do NOT receive user messages directly.
