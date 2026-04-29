# Core Memory Layer

## Purpose
Store only stable, high-confidence anchors. This layer is the most protected — changes require composite score ≥ 0.80 AND stability ≥ 0.85.

## What Belongs Here
- Long-term investment principles that guide decision-making
- Immutable user preferences and constraints
- Core agent behavioral rules (from harness constitution)
- Critical identity facts (who the user is, what they value)
- Stable decision frameworks that have been repeatedly validated

## What Does NOT Belong Here
- Current market data or temporary analysis
- Unverified hypotheses
- Speculative theses
- Detailed research notes (those go in long_term or fact_store)
- Session state or working context

## Entry Template

Each core memory entry must include:

```markdown
---
id: core_<YYYYMMDD>_<seq>
type: <principle | preference | identity | framework>
layer: core
importance: 0.9-1.0
stability: 0.85-1.0
confidence: 0.85-1.0
status: active
since: <ISO8601 — when this became core>
last_reviewed: <ISO8601>
review_due: <ISO8601 — 180 days from last_reviewed>
tags: [<domain tags>]
---

## <Title>

<Concise statement of the core memory — 2-4 sentences max>

### Why Core
<Why this is stable enough and important enough to be core>

### Validations
- <Source 1 + date>
- <Source 2 + date>
- <Source 3 + date>

### Related
- Long-term details: `memory/long_term/<file>.md`
- Fact store: `fact_store/<path>`
- Graph node: `<neo4j_node_id>` (if applicable)
```

## Review Schedule
- Every 180 days, re-validate stability and core-worthiness
- If composite drops below 0.75, demote to long-term
