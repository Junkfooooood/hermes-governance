# Hook Catalog

## Purpose

Hooks are interception points in the agent lifecycle where harness rules are enforced. They allow the harness to inspect, validate, modify, or block agent actions without the agent needing to remember every rule.

Hooks run OUTSIDE the agent's decision loop — they are harness-level enforcement, not agent self-discipline.

## Hook Types

### Session Hooks

| Hook | When It Fires | Purpose |
|------|--------------|---------|
| `pre_session_start` | Before agent initialization | Validate environment, load rules, check credentials |
| `post_session_start` | After agent is initialized | Set up audit trail, register with coordinator |
| `pre_session_end` | Before cleanup begins | Flush pending writes, prepare feedback records |
| `post_session_end` | After cleanup completes | Archive session, update metrics, release resources |

### Turn Hooks

| Hook | When It Fires | Purpose |
|------|--------------|---------|
| `pre_turn` | Before each API call | Prefetch memories, check noise ratio, validate context |
| `post_turn` | After each API call | Record turn outcome, update noise metrics |

### Tool Hooks

| Hook | When It Fires | Purpose |
|------|--------------|---------|
| `pre_tool_call` | Before tool execution | Validate parameters, check permissions, confirm safety |
| `post_tool_call` | After tool execution | Audit result, scan for secrets, check for anomalies |

### Delegation Hooks

| Hook | When It Fires | Purpose |
|------|--------------|---------|
| `pre_delegation` | Before delegation contract is issued | Validate contract completeness, check scope |
| `post_delegation` | After child agent returns results | Verify result format, check against contract |
| `pre_child_spawn` | Before spawning a child agent | Validate spawn limits, check resource availability |

### Review Hooks

| Hook | When It Fires | Purpose |
|------|--------------|---------|
| `pre_review` | Before reviewer evaluates output | Strip executor reasoning (PGE pattern) |
| `post_review` | After reviewer returns verdict | Log verdict, route to coordinator |

### Error Hooks

| Hook | When It Fires | Purpose |
|------|--------------|---------|
| `on_error` | On any error or exception | Classify error, decide recovery strategy |
| `on_safety_alert` | On safety rule violation | Immediate escalation, pause affected agents |
| `on_noise_alert` | When context noise exceeds threshold | Trigger compression or offloading |

## Hook Implementation

Hooks are implemented as:
- **Python callbacks** in `.hermes/hooks/` (for the hermes-agent runtime)
- **Natural-language checklists** in harness rules (for agent self-enforcement)

Runtime hooks take precedence — they cannot be bypassed by the agent.

### Hook Contract

Every hook implementation must:
1. Accept a context object with relevant state
2. Return one of: `ALLOW` (proceed), `MODIFY` (proceed with changes), `BLOCK` (stop with reason), `ESCALATE` (defer to coordinator/human)
3. Be non-blocking (fast execution, no network calls unless essential)
4. Log its decision for audit

### Hook Configuration

Hooks are enabled/disabled in `config.yaml`:

```yaml
harness:
  hooks:
    pre_tool_call: true
    post_tool_call: true
    pre_session_start: true
    pre_delegation: true
    on_safety_alert: true
    on_noise_alert: true
```

Hooks related to safety and session integrity should NOT be disabled.
