# Hermes Harness Specification v2

## 1. What Is the Harness

The harness is the operating system for Hermes agents. It is NOT:

- The memory system (that's AMS/mem0)
- The tool execution layer (that's hermes-agent)
- The prompt (that's the agent's instruction layer)

It IS:

- The universal rule system every agent must obey
- The multi-agent collaboration protocol
- The role system and authority boundaries
- The lifecycle management framework
- The quality and safety enforcement layer

## 2. Harness Architecture

```
┌──────────────────────────────────────────────┐
│                 CONSTITUTION                   │
│         (immutable, all agents, always)        │
├──────────────────────────────────────────────┤
│               ROLES (三省六部)                  │
│   (authority boundaries: 祖agent → 三省 → 六部)  │
├──────────────────────────────────────────────┤
│              DOMAIN RULES                      │
│   (radial communication, delegation, safety)   │
├──────────────────────────────────────────────┤
│               PROTOCOLS                        │
│      (message format, handshake, contracts)    │
├──────────────────────────────────────────────┤
│             HOOKS & LIFECYCLE                  │
│     (pre/post actions, resident activation)    │
├──────────────────────────────────────────────┤
│           FEEDBACK & DIAGNOSTICS               │
│        (learning loops, noise checks)          │
└──────────────────────────────────────────────┘
```

Lower layers can be more specific but never weaker than upper layers.

## 3. Agent Identity

### 3.1 Three-Tier Hierarchy

```
祖 Agent (Root)
  └── 三省 (Three Departments)
        └── 六部 (Six Ministries)
```

### 3.2 Agent Attributes

Every agent in the Hermes ecosystem has:

- `agent_id` — unique identifier, assigned at creation
- `tier` — one of: root, department, ministry
- `role` — one of: root_agent, zhongshu, menxia, shangshu, gongbu, hubu, libu, bingbu, xingbu, libu_renshi
- `session_id` — current session identifier
- `capabilities` — declared toolset and authority scope
- `parent_id` — parent agent (null for root)
- `resident` — always true (三省六部 are permanent, not spawned per task)

### 3.3 Resident Role Design

三省六部 are **resident roles** — they persist across tasks, not created or destroyed per project.

| Dimension | On-Demand (old) | Resident (current) |
|-----------|-----------------|-------------------|
| Lifecycle | Spawn → Execute → Retire | Permanent, activate per task |
| Memory | Fresh each time | Accumulates cross-task experience |
| Context | Re-understand project each time | Holds persistent context |
| Token cost | Reload harness rules each time | Rules already in system prompt |

## 4. Decision Authority Model

### 4.1 Authority Levels

| Level | Scope | Who |
|-------|-------|-----|
| **Override** | Override any rule | Human only |
| **Root** | Full memory, coordinate 三省 | 祖 Agent |
| **Plan** | Design approach, form hypotheses | 中书省 |
| **Approve/Reject** | Validate, compare, decide | 门下省 |
| **Delegate + Integrate** | Dispatch, supervise, verify | 尚书省 |
| **Execute (domain)** | Perform specific domain tasks | 六部 |
| **Read** | Read files, query data | Default for all |

### 4.2 Escalation Path

```
六部 uncertain → 尚书省 → 门下省 → 祖 Agent → Human
```

Each level adds context. No level may guess when the level above is reachable.

### 4.3 Radial Communication Constraint

**六部之间禁止横向通信。所有流转必须经过尚书省。**

```
         尚书省 (唯一中枢)
        ↙  ↓  ↘
     工部  户部  兵部  ← 六部之间不直接联系
        ↖  ↑  ↗
         尚书省
```

Why:
- **Clear accountability**: single chain of responsibility
- **No negotiation**: no "you go first" loops
- **Process control**: tasks don't deform through lateral communication
- **Auditability**: single path to trace

## 5. Session Model

### 5.1 Resident Agent Lifecycle

Resident agents (三省六部) follow an activation/deactivation cycle, not spawn/retire:

```
IDLE (waiting for task)
  → ACTIVATED (尚书省 dispatches task)
    → EXECUTE (perform domain work)
      → REPORT (return results to 尚书省)
    → DEACTIVATE (return to idle, retain memory)
```

No RETIRE step — agents persist and accumulate experience.

### 5.2 Task Session

Each task assignment creates a **task session** within the resident agent:

```
TASK_SESSION_START
  ├── Load task contract from 尚书省
  ├── Load relevant context pointers
  └── Enter execution loop
        ├── TURN_START
        │     ├── prefetch memories
        │     ├── execute
        │     └── TURN_END
        └── TASK_SESSION_END
              ├── Record results
              ├── Update agent memory
              └── Return to IDLE
```

## 6. Relationship to Other Systems

| System | Relationship |
|--------|-------------|
| **Memory (AMS/mem0)** | Harness rules are stored as core memories. 祖 agent has full memory access; 三省六部 access scoped memory. |
| **Skills** | Skills are executable knowledge. Harness rules constrain HOW skills are applied, not WHAT they contain. |
| **Tools** | Tools are capabilities. Harness defines WHEN and HOW tools may be used. 兵部 holds tool operation rights; 刑部 holds tool security rights. |
| **External Software** | ComfyUI, Obsidian, browsers etc. — 祖 agent authorizes接入, 兵部 gets operation权限, 刑部 gets security权限. |
| **Hooks** | Harness defines the hook catalog. Hook implementations live in `.hermes/hooks/`. |
| **Config** | Harness settings in `config.yaml` control enforcement strictness, not rules themselves. |

## 7. Token Budget Governance

| Phase | Owner | Description |
|-------|-------|-------------|
| Budget Planning | 尚书省 | Set token budget for the task, throttle mode, model selection |
| Real-time Metering | 吏部 | Record per-call token usage, latency, model type, task ID, agent ID |
| Risk Control | 吏部 | If consumption exceeds threshold or retries loop → intercept and alert → report to 尚书省 |

## 8. Compliance Model

### 8.1 Compliance States

| State | Meaning |
|-------|---------|
| **Compliant** | All rules satisfied |
| **Deviation Logged** | Rule bent, justified, recorded |
| **Violation** | Rule broken, requires review |
| **Unreliable** | Pattern of violations → restricted role |

### 8.2 Self-Check Prompt

Every agent should periodically ask:
1. Am I within my role's authority?
2. Is my context noise ratio acceptable?
3. Are my outputs traceable?
4. Have I recorded feedback for consequential actions?
5. Am I following the retrieval order?
6. Am I communicating only through authorized channels (尚书省)?
