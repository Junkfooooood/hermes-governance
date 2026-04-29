# Feedback Loop

## Purpose

The feedback loop is how Hermes agents learn from reality — the mechanism that turns one-shot task execution into cumulative improvement. It implements Law 6 (Learning from Reality).

## The Loop

```
┌──────────────────┐
│  1. HYPOTHESIS   │  ← Expected outcome, based on knowledge + assumptions
└───────┬──────────┘
        ▼
┌──────────────────┐
│   2. ACTION      │  ← Execute with trace_id
└───────┬──────────┘
        ▼
┌──────────────────┐
│   3. OBSERVE     │  ← Collect real-world outcome
└───────┬──────────┘
        ▼
┌──────────────────┐
│   4. COMPARE     │  ← Expected vs. Actual
└───────┬──────────┘
        ▼
┌──────────────────┐
│   5. UPDATE      │  ← Adjust confidence, promote/demote knowledge
└───────┬──────────┘
        ▼
┌──────────────────┐
│   6. RECORD      │  ← Write feedback entry for future retrieval
└──────────────────┘
```

## When to Record Feedback

Not every action needs a feedback record. Record when:

| Trigger | Example |
|---------|---------|
| **Outcome ≠ Expected** | Test failed when it should have passed |
| **New information** | User corrected a factual claim |
| **Decision point** | Chose approach A over B, want to track if A was right |
| **External validation** | User confirmed or rejected agent output |
| **Methodology test** | Applied a new method, want to track its effectiveness |
| **Safety incident** | Near-miss or actual safety violation |

## Feedback Record Format

```yaml
feedback_id: fb_<YYYYMMDD>_<seq>
related_memory_id: <memory object id, if applicable>
related_delegation_id: <delegation id, if applicable>
trace_id: <uuid>

hypothesis:
  statement: <what was expected>
  confidence_before: 0.0-1.0
  basis: <what knowledge/assumption this was based on>

action:
  description: <what was done>
  timestamp: <ISO8601>
  agent_id: <agent that performed the action>

outcome:
  result: SUCCESS | PARTIAL | FAILURE | UNEXPECTED
  actual: <what actually happened>
  gap: <difference between expected and actual, if any>
  evidence: <pointer to output, logs, user confirmation>

update:
  confidence_after: 0.0-1.0
  knowledge_change: NONE | ADJUSTED | PROMOTED | DEMOTED | DEPRECATED
  reason: <why the confidence changed>
  affected_memories: [<list of memory IDs that were updated>]

timestamp: <ISO8601>
```

## Feedback Routing

```
Feedback recorded by agent
  → AMS evaluates feedback significance
    → Low significance: stored in session log only
    → Medium significance: updates affected memory weights
    → High significance: triggers memory promotion/demotion
    → Critical: triggers constitution review (human-in-loop)
```

## Feedback-Driven Memory Updates

| Outcome Pattern | Memory Action |
|-----------------|---------------|
| Hypothesis confirmed 3+ times | Promote to long-term |
| Hypothesis confirmed, high stability | Consider core promotion |
| Hypothesis invalidated once | Reduce confidence, keep in short-term |
| Hypothesis invalidated 2+ times | Demote to archive with invalidation note |
| Methodology consistently effective | Promote skill to active |
| Methodology consistently ineffective | Deprecate skill |

## Feedback Cleanup

- Feedback records have a TTL: 90 days default
- After TTL, they are archived, not deleted
- Archived feedback is excluded from default recall but queryable for audits
- Exception: safety incident feedback is kept permanently
