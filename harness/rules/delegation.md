# Delegation Rules

## 1. The Delegation Contract

Every task handoff must use a delegation contract. No contract = no execution.

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `delegation_id` | Unique identifier | `del_20260428_001` |
| `task` | Clear, specific task description | "Add rate limiting to the auth middleware" |
| `success_criteria` | Verifiable conditions | "Tests pass, rate limit triggers at 100req/min, returns 429" |
| `context_scope` | What files/docs the child can access | `["src/auth/", "docs/auth-flow.md"]` |
| `authority` | What the child is allowed to do | `["read", "write_files", "run_tests"]` |
| `deadline` | ISO8601 timestamp | `2026-04-28T15:00:00Z` |
| `result_format` | Expected return schema | Open-ended text, structured JSON, file path |

### Optional Fields

| Field | Description |
|-------|-------------|
| `dependencies` | Other delegation IDs this task depends on |
| `max_iterations` | Maximum Ralph Loop cycles (default: 3) |
| `priority` | low / normal / high / critical |
| `parent_context` | Additional background beyond scope |

## 2. Contract Lifecycle

```
DRAFT (coordinator)
  → ISSUED (sent to executor)
    → ACKNOWLEDGED (executor confirmed understanding)
      → IN_PROGRESS (execution started)
        → COMPLETED (result returned)
          → UNDER_REVIEW (reviewer evaluating)
            → APPROVED | REVISED | REJECTED (final state)
        → BLOCKED (executor cannot proceed)
          → REVISED (coordinator updates contract)
        → TIMED_OUT (deadline exceeded)
          → coordinator decides: extend or reassign
```

## 3. Context Scope Rules

The `context_scope` field defines what information the child agent can access.

- **Minimal by default**: only include what the task actually needs.
- **Explicit paths only**: no wildcard access (no `src/**/*`).
- **No transitive access**: the child cannot access files referenced by the granted files unless also explicitly listed.
- **No memory access**: child agents start without memory preload unless `context_scope` includes specific memory pointers.

## 4. Authority Boundaries

The `authority` field is an allowlist, not a blocklist.

| Authority Level | Includes |
|----------------|----------|
| `read` | Read files, query databases, fetch URLs |
| `write_files` | Create and modify files within scope |
| `run_commands` | Execute shell commands (non-destructive) |
| `run_tests` | Execute test suites |
| `git_ops` | Git operations (branch, commit — not force-push) |
| `external_api` | Call external APIs (with coordinator-approved endpoints) |

If an executor needs an authority not in the contract, it must request a contract revision.

## 5. Timeout & Fallback

- Executor must report progress if execution exceeds 50% of deadline.
- If deadline is reached without a result, the coordinator may:
  - Extend the deadline (once, max +50%)
  - Reassign to a different executor
  - Accept partial results
  - Abandon the task
- Executor must NOT silently continue past the deadline.

## 6. Delegation Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| "Do your best" | No success criteria | Define verifiable outcome |
| "Fix the bug" | No scope | Specify which files, what the expected behavior is |
| "Make it better" | Subjective | Define measurable improvement |
| Delegating to 5+ agents at once | Coordination overhead exceeds benefit | Limit to 3 concurrent, queue the rest |
| Delegating delegations | Authority leakage | max_spawn_depth = 1 |
