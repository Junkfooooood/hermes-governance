# Noise Monitor — Implementation v1

## 1. Purpose

Context noise is the #1 enemy of agent performance. The noise monitor measures, reports, and triggers remediation when context quality degrades. It implements the noise control policy from the memory governance spec and harness Law 5.

## 2. Noise Taxonomy

### Noise Categories

| Category | Definition | Example |
|----------|-----------|---------|
| **Redundant** | Same information appears multiple times | Same fact in memory + skill + system prompt |
| **Low-value** | Information that doesn't contribute to the task | Generic greetings, formatting noise |
| **Stale** | Information that was once useful but no longer is | Past turn details no longer relevant |
| **Pointerable** | Full text that could be replaced by a pointer | Full research report when summary would do |
| **Out-of-scope** | Information unrelated to the current task | Prefetched memories for a different domain |

### Noise Ratio Formula

```
noise_ratio = (redundant_chars + low_value_chars + stale_chars + pointerable_chars + out_of_scope_chars) / total_context_chars
```

## 3. Token Budget Allocation

A finite context window requires a budget. Suggested allocation for a 100K token context:

| Budget Category | Max Tokens | % of Context |
|----------------|------------|-------------|
| **System prompt + Constitution** | 3,000 | 3% |
| **Role definition + Rules** | 2,000 | 2% |
| **Core memory pointers** | 500 | 0.5% |
| **Task-relevant memory recall** | 5,000 | 5% |
| **Current task context** | 15,000 | 15% |
| **Conversation history (recent)** | 20,000 | 20% |
| **Tool results (current turn)** | 10,000 | 10% |
| **Reserved for reasoning** | 44,500 | 44.5% |

### Budget Enforcement
- When a category exceeds its budget, trim or compress.
- Core memory and constitution have fixed budgets — they are non-negotiable.
- Conversation history budget shrinks first when context is tight.
- Tool results older than 3 turns are summarized, not kept verbatim.

## 4. Noise Detection Triggers

Run noise diagnostic when:

| Trigger | Why |
|---------|-----|
| **Session start** | Establish baseline |
| **Every 10 turns** | Detect gradual drift |
| **Context > 70% full** | Preventive check before compression forces data loss |
| **Agent reports feeling "unfocused"** | Subjective signal is often early warning |
| **After loading a large skill or memory block** | Check impact of the addition |
| **Coordinator request** | Multi-agent health check |

## 5. Remediation Actions

### Level 1: Noise Ratio 0–20% — Healthy
No action.

### Level 2: Noise Ratio 21–35% — Elevated
- Deduplicate: remove any content appearing more than once
- Pointerize: replace full-text memories with pointers where available
- Summarize: compress tool results older than 3 turns to one-line summaries

### Level 3: Noise Ratio 36–50% — High
All Level 2 actions, plus:
- Truncate conversation history to last 10 turns
- Evict low-importance prefetched memories (re-fetch on demand)
- Defer non-essential skill loading
- Report to coordinator

### Level 4: Noise Ratio > 50% — Critical
All Level 3 actions, plus:
- Force context compression immediately
- Keep only: constitution, role, current task, last 5 turns
- Re-run noise diagnostic after compression
- Escalate to coordinator with before/after noise ratio

## 6. Noise Report Format

```yaml
noise_report:
  timestamp: <ISO8601>
  agent_id: <id>
  session_id: <id>
  turn_number: <int>

  context_composition:
    system_prompt_pct: <float>
    memory_pct: <float>
    conversation_pct: <float>
    tool_results_pct: <float>
    other_pct: <float>

  noise_breakdown:
    redundant_pct: <float>
    low_value_pct: <float>
    stale_pct: <float>
    pointerable_pct: <float>
    out_of_scope_pct: <float>
    total_noise_pct: <float>

  top_noise_sources:
    - source: <description>
      category: <noise_category>
      chars: <int>
      recommendation: <action>

  actions_taken:
    - <action 1>
    - <action 2>

  noise_after: <float>  # post-remediation noise ratio
```

## 7. Auto-Compression Rules

When compression is triggered (noise > 50% or config threshold), the auto-compressor:

1. **Preserves** (always kept):
   - Constitution and core principles
   - Role definition
   - Current task description
   - Last 5 turns of conversation
   - Pending action items

2. **Compresses** (summarized, not deleted):
   - Turns 6–20: compressed to 2-line summaries each
   - Tool results older than 3 turns: result summary only
   - Prefetched memories not referenced in last 5 turns: pointer only

3. **Removes** (deleted from context, re-fetchable):
   - Turns beyond 20: removed entirely (queryable via session search)
   - Low-importance memories not referenced
   - Skill definitions not used in current session
   - Verbose tool output already summarized

## 8. Integration with AMS

The noise monitor feeds into AMS:
- High noise sustained across sessions → AMS flags memory bloat
- Frequently pointerable content → AMS converts to pointer-only storage
- Repeatedly stale memories → AMS reduces their confidence score
