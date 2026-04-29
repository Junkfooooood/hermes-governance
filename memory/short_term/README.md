# Short-term Memory Layer

## Purpose
Store recent context, temporary hypotheses, and pending follow-ups. This layer has a mandatory TTL — entries that are not promoted or explicitly renewed will be archived when TTL expires.

## What Belongs Here
- Active hypotheses awaiting validation
- Recent task context that spans multiple sessions
- Temporary analysis conclusions (not yet verified)
- Current event observations with short relevance windows
- Pending follow-ups and action items
- Intermediate research outputs before final validation

## What Does NOT Belong Here
- Validated reusable knowledge (→ long_term)
- Ephemeral working state (→ working, discard after session)
- Core principles (→ core)
- Completed one-shot tasks with no follow-up (→ archive)

## Entry Template

```markdown
---
id: stm_<YYYYMMDD>_<seq>
type: <hypothesis | context | observation | follow_up>
layer: short_term
importance: <0.0–1.0>
stability: <0.0–1.0>
confidence: <0.0–1.0>
status: active
created: <ISO8601>
ttl: P<ND>D  (ISO 8601 duration, default P30D)
expires: <ISO8601>
review_due: <ISO8601 — at TTL expiry>
tags: [<domain tags>]
promotion_conditions: <what would move this to long_term>
---

## <Title>

### Current State
<What we know now>

### Open Questions
- <Question 1>
- <Question 2>

### Hypothesis/Prediction
<What we expect, if applicable>

### Next Checkpoint
<When to re-evaluate, what to look for>
```

## TTL Guidelines

| Type | Default TTL | Rationale |
|------|-------------|-----------|
| Hypothesis | P30D | Long enough to gather evidence; short enough to not linger |
| Task Context | P7D | Task should complete or be re-scoped within a week |
| Market Observation | P7D | Market data decays fast |
| Follow-up Item | P14D | Action items need timely resolution |
| Interim Analysis | P21D | Give time for validation before archiving |

## Auto-Archival
When TTL expires, AMS evaluates:
- Was this referenced recently? → Extend TTL by 50%
- Has it been validated? → Consider promotion to long_term
- Neither? → Archive with reason "TTL expired"
