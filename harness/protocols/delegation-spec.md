# Delegation Contract Specification

## Purpose

The delegation contract is the formal handoff document for every task in the Hermes system. It defines WHAT to do, HOW to verify success, WHAT resources are available, and WHAT authority is granted.

No delegation contract = no execution. This is a hard rule.

## Contract Schema

```yaml
delegation_id: del_<YYYYMMDD>_<seq>     # Required. Unique task identifier.
task: <string>                            # Required. Specific, actionable description.
success_criteria:                         # Required. Verifiable conditions.
  - <condition 1>
  - <condition 2>
context_scope:                            # Required. What the 六部 agent can access.
  files:                                  # Explicit file/directory paths.
    - path/to/file
  memory_pointers:                        # Optional. Memory entries to preload.
    - memory/long_term/schema.md
  external_data:                          # Optional. External data sources.
    - url: <endpoint>
      purpose: <why this is needed>
authority:                                # Required. Allowed operations.
  - read
  - write_files
  - run_commands
  - run_tests
  - tool_invoke
  - external_api
deadline: <ISO8601>                       # Required. Hard stop timestamp.
result_format:                            # Required. Expected output structure.
  type: text | json | file | multi_part
  schema: <description or JSON Schema>
  destination: <where to write, if type is file>
ministry: <target_ministry>               # Required. Which 六部 handles this.
max_iterations: 3                         # Optional. Max execution cycles (default 3).
priority: normal                          # Optional. low | normal | high | critical.
token_budget: <number>                    # Optional. Token limit for this sub-task.
dependencies:                             # Optional. Other delegation IDs.
  - del_<id>
notes: <string>                           # Optional. Additional context.
```

## Field Definitions

### `task`
- Must be specific enough that a 六部 agent with no prior context can understand it.
- Must be actionable (not "think about X" but "do X and report Y").
- Bad: "Improve the authentication system."
- Good: "Add rate limiting to the login endpoint: max 5 attempts per IP per minute, return 429 on exceed, write test that verifies the limit triggers."

### `success_criteria`
- Must be verifiable by 门下省 without the executing agent's reasoning.
- Each criterion must be binary (either met or not met — no partial grades).
- Bad: "The code should be good."
- Good: "1) `npm test` passes. 2) Login returns 429 after 5 requests in <60s. 3) Existing auth tests still pass."

### `context_scope`
- Explicit allowlist of what the 六部 agent can access.
- Agent must NOT access files outside this list.
- If the task requires accessing a file referenced by a granted file, it must be explicitly listed.
- Empty `context_scope` means the agent works only from the task description.

### `authority`
- Explicit allowlist of what operations the 六部 agent may perform.
- If an agent needs an authority not listed, it must request a contract revision.
- Authority levels in ascending power: `read` < `write_files` < `run_commands` < `run_tests` < `tool_invoke` < `external_api`.

### `deadline`
- Hard stop. Agent must report (partial results or blocker) by this time.
- 尚书省 may extend once, by at most 50% of original duration.
- Set realistic deadlines. "ASAP" is not a deadline.

### `ministry`
- Specifies which 六部 agent handles this delegation.
- Determined by 尚书省 based on action type:

| Action Type | Ministry |
|-------------|----------|
| 产出型 (code/file/content) | 工部 |
| 数据型 (data/knowledge/assets) | 户部 |
| 表达型 (report/summary/presentation) | 礼部 |
| 自动型 (software/workflow/batch) | 兵部 |
| 校验型 (security/test/risk) | 刑部 |
| 治理型 (status/priority/record) | 吏部 |

### `token_budget`
- Optional token limit for this sub-task.
- 吏部 monitors consumption in real-time.
- Alert at 80% consumption, hard stop at 120%.

## Contract Lifecycle

```
DRAFT (尚书省)
  → DISPATCHED (sent to 六部)
    → ACKNOWLEDGED (六部 confirmed understanding)
      → IN_PROGRESS (execution started)
        → COMPLETED (result returned to 尚书省)
          → VERIFIED (尚书省 checks result)
            → ACCEPTED | REVISED | REJECTED
        → BLOCKED (六部 cannot proceed)
          → REVISED (尚书省 updates contract)
        → TIMED_OUT (deadline exceeded)
          → 吏部 alerts 尚书省 → extend or reassign
```

## Contract Revision

If a 六部 agent needs changes to the contract:
1. Agent sends `QUERY` to 尚书省 with specific requested changes
2. 尚书省 evaluates and either:
   - Issues revised contract (`DISPATCH` with same `delegation_id` and `revision: N+1`)
   - Denies the revision and instructs agent to proceed with original contract
3. Agent must NOT unilaterally modify the contract

## Contract Termination

A contract is terminated when:
- 尚书省 verifies result and marks `ACCEPTED` (success)
- 尚书省 marks `REJECTED` + decides not to re-delegate (failure)
- Deadline exceeded + 尚书省 decides not to extend (timeout)
- `ALERT` from 六部 agent that cannot be resolved within session (blocked)
