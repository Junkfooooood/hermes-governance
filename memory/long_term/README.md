# Long-term Memory Layer

## Purpose
Store validated, reusable knowledge. This is the workhorse layer — most durable knowledge lives here. Entries here have been confirmed as useful and stable enough to keep beyond the current task or session.

## What Belongs Here
- Validated research conclusions with evidence chains
- Proven methodologies and analytical frameworks
- Industry knowledge, company deep-dives, sector analyses
- Stable facts that have been cross-referenced
- Recurring patterns observed across multiple instances
- Templates and schemas for repeated analysis tasks

## What Does NOT Belong Here
- Unvalidated hypotheses (→ short_term)
- Current session state (→ working)
- One-time observations (→ discard or short_term with short TTL)
- Core principles stable enough for SOUL.md level (→ core)

## Entry Template

```markdown
---
id: ltm_<YYYYMMDD>_<seq>
type: <research_conclusion | methodology | industry_knowledge | pattern | fact>
layer: long_term
importance: <0.0–1.0>
stability: <0.0–1.0>
confidence: <0.0–1.0>
status: active
created: <ISO8601>
last_reviewed: <ISO8601>
review_due: <ISO8601 — 90 days from last_reviewed>
tags: [<domain tags>]
pointer: <path to full content if stored elsewhere>
---

## <Title>

### Summary
<2-4 sentence summary>

### Evidence Chain
- Source 1: <what, when, confidence contribution>
- Source 2: <what, when, confidence contribution>
- Validation: <real-world feedback received>

### Related Memories
- Core: `memory/core/<file>.md`
- Fact Store: `fact_store/<path>`
- Short-term predecessors: `memory/short_term/<file>.md`
- Neo4j Node: `<node_id>`
```

## Review Schedule
- Every 90 days, re-score and check for staleness
- If composite drops below 0.50 → demote to short_term
- If composite ≥ 0.80 and stability ≥ 0.85 → promote to core candidate
