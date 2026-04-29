# Hermes Harness Specification v1

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
│                    ROLES                       │
│     (authority boundaries per agent type)      │
├──────────────────────────────────────────────┤
│              DOMAIN RULES                      │
│   (collaboration, delegation, safety, etc.)    │
├──────────────────────────────────────────────┤
│               PROTOCOLS                        │
│      (message format, handshake, contracts)    │
├──────────────────────────────────────────────┤
│             HOOKS & LIFECYCLE                  │
│     (pre/post actions, session boundaries)     │
├──────────────────────────────────────────────┤
│           FEEDBACK & DIAGNOSTICS               │
│        (learning loops, noise checks)          │
└──────────────────────────────────────────────┘
```

Lower layers can be more specific but never weaker than upper layers.

## 3. Agent Identity

Every agent in the Hermes ecosystem has:

- `agent_id` — unique identifier, assigned at spawn
- `role` — one of: coordinator, executor, reviewer, specialist
- `session_id` — current session identifier
- `capabilities` — declared toolset and authority scope
- `parent_id` — spawning agent (null for root)

## 4. Decision Authority Model

### 4.1 Authority Levels

| Level | Scope | Example |
|-------|-------|---------|
| **Read** | Read files, query databases, fetch URLs | Default for all agents |
| **Suggest** | Propose changes, draft code | Executor in planning phase |
| **Execute** | Write files, run commands | Executor during execution phase |
| **Approve** | Sign off on executor output | Reviewer, Coordinator |
| **Delegate** | Spawn child agents | Coordinator only |
| **Override** | Override safety rules | Human only |

### 4.2 Escalation Path

```
Executor uncertain → Reviewer → Coordinator → Human
```

Each level adds context. No level may guess when the level above is reachable.

## 5. Session Model

Every agent session follows this lifecycle:

```
SESSION_START
  ├── Load AGENTS.md
  ├── Load role definition
  ├── Load constitution
  ├── Handshake with coordinator (if child)
  └── Enter execution loop
        │
        ├── TURN_START
        │     ├── prefetch memories
        │     ├── pre_tool_call hooks
        │     ├── execute
        │     ├── post_tool_call hooks
        │     └── TURN_END
        │
        ├── [delegation to child agent]
        ├── [review cycle]
        │
        └── SESSION_END
              ├── on_session_end hooks
              ├── feedback recording
              ├── memory promotion/demotion
              └── cleanup
```

## 6. Relationship to Other Systems

| System | Relationship |
|--------|-------------|
| **Memory (AMS/mem0)** | Harness rules are stored as core memories. AMS governs memory lifecycle; harness governs agent behavior. |
| **Skills** | Skills are executable knowledge. Harness rules constrain HOW skills are applied, not WHAT they contain. |
| **Tools** | Tools are capabilities. Harness defines WHEN and HOW tools may be used. |
| **Hooks** | Harness defines the hook catalog. Hook implementations live in `.hermes/hooks/`. |
| **Config** | Harness settings in `config.yaml` control enforcement strictness, not rules themselves. |

## 7. Compliance Model

### 7.1 Compliance States

| State | Meaning |
|-------|---------|
| **Compliant** | All rules satisfied |
| **Deviation Logged** | Rule bent, justified, recorded |
| **Violation** | Rule broken, requires review |
| **Unreliable** | Pattern of violations → restricted role |

### 7.2 Self-Check Prompt

Every agent should periodically ask:
1. Am I within my role's authority?
2. Is my context noise ratio acceptable?
3. Are my outputs traceable?
4. Have I recorded feedback for consequential actions?
5. Am I following the retrieval order?
