# Delegation Contract Specification

## Purpose

The delegation contract is the formal handoff document for every task in the Hermes multi-agent system. It defines WHAT to do, HOW to verify success, WHAT resources are available, and WHAT authority is granted.

No delegation contract = no execution. This is a hard rule.

## Contract Schema

```yaml
delegation_id: del_<YYYYMMDD>_<seq>     # Required. Unique task identifier.
task: <string>                            # Required. Specific, actionable description.
success_criteria:                         # Required. Verifiable conditions.
  - <condition 1>
  - <condition 2>
context_scope:                            # Required. What the executor can access.
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
deadline: <ISO8601>                       # Required. Hard stop timestamp.
result_format:                            # Required. Expected output structure.
  type: text | json | file | multi_part
  schema: <description or JSON Schema>
  destination: <where to write, if type is file>
max_iterations: 3                         # Optional. Max Ralph Loop cycles (default 3).
priority: normal                          # Optional. low | normal | high.
dependencies:                             # Optional. Other delegation IDs.
  - del_<id>
notes: <string>                           # Optional. Additional context.
```

## Field Definitions

### `task`
- Must be specific enough that an executor with no prior context can understand it.
- Must be actionable (not "think about X" but "do X and report Y").
- Bad: "Improve the authentication system."
- Good: "Add rate limiting to the login endpoint: max 5 attempts per IP per minute, return 429 on exceed, write test that verifies the limit triggers."

### `success_criteria`
- Must be verifiable by a reviewer without the executor's reasoning.
- Each criterion must be binary (either met or not met — no partial grades).
- Bad: "The code should be good."
- Good: "1) `npm test` passes. 2) Login returns 429 after 5 requests in <60s. 3) Existing auth tests still pass."

### `context_scope`
- Explicit allowlist of what the executor can access.
- Executor must NOT access files outside this list.
- If the task requires accessing a file referenced by a granted file, it must be explicitly listed.
- Empty `context_scope` means the executor works only from the task description.

### `authority`
- Explicit allowlist of what operations the executor may perform.
- If an executor needs an authority not listed, it must request a contract revision.
- Authority levels in ascending power: `read` < `write_files` < `run_commands` < `run_tests` < `git_ops` < `external_api`.

### `deadline`
- Hard stop. Executor must report (partial results or blocker) by this time.
- Coordinator may extend once, by at most 50% of original duration.
- Set realistic deadlines. "ASAP" is not a deadline.

### `result_format`
- Defines the shape of the expected output.
- `text`: Free-form natural language.
- `json`: Structured JSON with a defined schema.
- `file`: Output written to a specific file path (included in REPORT).
- `multi_part`: Combination (e.g., code changes + summary text).

## Contract Revision

If an executor needs changes to the contract:
1. Executor sends `QUERY` with specific requested changes
2. Coordinator evaluates and either:
   - Issues revised contract (`DELEGATE` with same `delegation_id` and `revision: N+1`)
   - Denies the revision and instructs executor to proceed with original contract
3. Executor must NOT unilaterally modify the contract

## Contract Termination

A contract is terminated when:
- `VERDICT` is `APPROVED` (success)
- `VERDICT` is `REJECTED` + coordinator decides not to re-delegate (failure)
- Deadline exceeded + coordinator decides not to extend (timeout)
- `ALERT` from executor that cannot be resolved within session (blocked)
