# Collaboration Rules

## 1. Agent Discovery

Agents are **resident roles** — they persist across sessions, not spawned per task. Discovery happens at system initialization, not per task.

### Initialization Flow
```
1. System starts → 祖 Agent initializes
2. 祖 Agent loads 三省 (中书省, 门下省, 尚书省)
3. 尚书省 initializes 六部 (工/户/礼/兵/刑/吏)
4. Each agent loads role definition + capabilities
5. 尚书省 maintains the active agent registry
```

### Capability Registry
Each agent registers at initialization:
```yaml
agent_id: agent_<role>
role: zhongshu | menxia | shangshu | gongbu | hubu | libu | bingbu | xingbu | libu_renshi
tier: san_sheng | liu_bu
capabilities:
  tools: [list of available tools]
  domain: [declared domain]
  authority: [authority level]
status: idle | active | busy
```

## 2. 尚书省 Authority

尚书省 is the single point of orchestration. It serves as **dispatcher**, **judge**, and **orchestrator**.

- 尚书省 assigns tasks to 六部, resolves conflicts, and aggregates results.
- No 六部 may delegate to another 六部 — all coordination goes through 尚书省.
- No 六部 may spawn child agents.
- 尚书省 decisions are final within the delegation scope.

### 尚书省 Responsibilities
- Task decomposition and sub-task packaging
- Dependency graph construction and optimization
- Deadline management and timeout monitoring
- Token budget governance (with 吏部 metering)
- Result integration and quality verification
- Conflict resolution between 六部

### Limits
- Must use delegation contracts for every task handoff
- Must track all active delegations
- Must not become a bottleneck — queue tasks if all 六部 are busy

## 3. Radial Communication

**All inter-agent communication flows through 尚书省. No lateral communication between 六部.**

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

## 4. Conflict Resolution

Priority order for resolving conflicts:
1. **Safety** — any safety flag overrides all other considerations (刑部)
2. **Constitution** — immutable laws override local rules
3. **Success Criteria** — output meeting criteria beats output that doesn't
4. **尚书省 Decision** — final arbitration within delegation scope

## 5. Shared State

Agents share state through pointers, not copies.

- Memory is read from the pointer layer (SOUL.md → memory.md → layer lookup).
- Agents do NOT copy memory into their context — they retrieve on demand.
- Write access to shared memory is governed by AMS, not by individual agents.
- Session state (working memory) is local to each agent and cleaned up on session end.

## 6. Task Flow

尚书省 manages the complete task flow:

```
1. 祖 Agent receives user request
2. 中书省 plans (hypothesis + validation action schema)
3. 门下省 reviews (info completeness + similar case search + missing degree)
4. 尚书省 dispatches to relevant 六部 (parallel where independent)
5. 六部 execute independently
6. 六部 report results to 尚书省
7. 尚书省 integrates results
8. 祖 Agent returns to user
```

六部 do NOT interrupt other 六部 mid-execution. Urgent safety flags bypass this rule — any agent may alert 尚书省 immediately.

## 7. Multi-Agent Sessions

- Each agent session is isolated (separate context window).
- Agents communicate only through structured messages (see [`protocols/message-spec.md`](../protocols/message-spec.md)).
- The 祖 Agent session is the only session that communicates directly with the human user.
- 六部 sessions do NOT receive user messages directly.
