# Delegation Rules

## 1. Delegation Chain

All delegation follows the fixed chain:

```
祖 Agent → 三省 (中书省 → 门下省 → 尚书省) → 六部
```

No skipping levels. No reverse delegation.

## 2. The Delegation Contract

Every task handoff must use a delegation contract. No contract = no execution.

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `delegation_id` | Unique identifier | `del_20260504_001` |
| `task` | Clear, specific task description | "整理这批网页资料到 Obsidian" |
| `success_criteria` | Verifiable conditions | "资料已归档到指定目录，笔记格式统一" |
| `context_scope` | What resources the agent can access | `["obsidian/vault/", "web/sources/"]` |
| `authority` | What the agent is allowed to do | `["read", "write_files", "browse"]` |
| `deadline` | ISO8601 timestamp | `2026-05-04T18:00:00Z` |
| `result_format` | Expected return schema | markdown / json / file_path |
| `ministry` | Target department | `hubu` / `gongbu` / etc. |

### Optional Fields

| Field | Description |
|-------|-------------|
| `dependencies` | Other delegation IDs this task depends on |
| `max_iterations` | Maximum execution cycles (default: 3) |
| `priority` | low / normal / high / critical |
| `token_budget` | Token limit for this sub-task |

## 3. Contract Lifecycle

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

## 4. 尚书省 Dispatch Logic

尚书省 determines which ministry handles each sub-task:

| Action Type | Ministry |
|-------------|----------|
| 产出型 (code/file/content) | 工部 |
| 数据型 (data/knowledge/assets) | 户部 |
| 表达型 (report/summary/presentation) | 礼部 |
| 自动型 (software/workflow/batch) | 兵部 |
| 校验型 (security/test/risk) | 刑部 |
| 治理型 (status/priority/record) | 吏部 |

## 5. Context Scope Rules

- **Minimal by default**: only include what the task actually needs
- **Explicit paths only**: no wildcard access
- **No transitive access**: cannot access files referenced by granted files
- **Pointer-based**: shared state through pointers, not copies

## 6. Authority Boundaries

| Authority Level | Includes |
|----------------|----------|
| `read` | Read files, query databases, fetch URLs |
| `write_files` | Create and modify files within scope |
| `run_commands` | Execute shell commands (non-destructive) |
| `run_tests` | Execute test suites |
| `browse` | Web browsing and automation |
| `tool_invoke` | Call external tools (ComfyUI, etc.) |
| `external_api` | Call external APIs |

## 7. Timeout & Fallback

- 六部 must report progress if execution exceeds 50% of deadline
- 吏部 monitors and alerts on timeout
- 尚书省 may: extend (once, max +50%), reassign, accept partial, or abandon

## 8. Delegation Anti-Patterns

| Anti-Pattern | Why It's Wrong | Fix |
|-------------|----------------|-----|
| "Do your best" | No success criteria | Define verifiable outcome |
| Delegating to all 6 ministries | Coordination overhead | Only assign relevant ones |
| 六部 self-assigning tasks | Breaks radial structure | Only 尚书省 dispatches |
| Skipping 尚书省 | Breaks delegation chain | Always go through the chain |
