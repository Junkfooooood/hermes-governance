# Feedback Loop — Generic Framework v1

## 1. Purpose

The feedback loop is the mechanism by which Hermes learns from reality. It closes the gap between expectation and outcome: hypothesis → action → observe → compare → update → record.

This file defines the **domain-agnostic** feedback framework. Domain-specific extensions (e.g., investment, health, learning) add domain-specific fields and scoring rules on top of this base.

## 2. The Universal Feedback Cycle

```
┌──────────────────────┐
│  1. FORM EXPECTATION │  ← What do we expect to happen?
│     (hypothesis)     │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  2. DEFINE CHECKPOINT│  ← When/how to verify?
│     (timeline)       │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  3. TAKE ACTION      │  ← Do something (or deliberately wait)
│     (optional)       │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  4. OBSERVE OUTCOME  │  ← What actually happened?
│     (data collection)│
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  5. COMPARE          │  ← Expected vs. Actual → gap analysis
│     (evaluation)     │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  6. UPDATE           │  ← Adjust confidence, refine model
│     (learning)       │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  7. RECORD           │  ← Write feedback, update memory weights
│     (persistence)    │
└──────────────────────┘
```

This cycle applies to ANY domain:
- **Investment**: thesis → market action → earnings/data → thesis update
- **Learning**: study method → practice → test result → method refinement
- **Health**: habit change → daily practice → measurement → habit adjustment
- **Relationships**: communication approach → interaction → response → approach refinement
- **Projects**: plan → execution → milestone → plan adjustment
- **Daily life**: prediction about anything → wait → actual outcome → update belief

## 3. Base Feedback Record Schema

```yaml
---
feedback_id: fb_<YYYYMMDD>_<seq>
domain: <domain tag — investment | learning | health | project | relationship | daily | ...>
type: <domain_specific_type>
related_memory_id: <memory object id>
related_graph_node: <Neo4j node id, if applicable>
timestamp: <ISO8601>
---

expectation:
  statement: <what was expected>
  confidence_before: 0.0-1.0
  basis: <what knowledge/assumption this was based on>
  timeline: <when was the outcome expected>

checkpoint:
  trigger: <what triggered the re-evaluation>
  metrics: <what data to check>

actual_outcome:
  result: CONFIRMED | PARTIALLY_CONFIRMED | INCONCLUSIVE | CONTRADICTED | INVALIDATED
  expected: <what was predicted>
  actual: <what actually happened>
  evidence: <pointer to data/source>

gap_analysis:
  gap_type: no_gap | minor_deviation | significant_deviation | complete_miss
  root_cause: <why did expected and actual diverge?>
  external_factors: <unforeseeable events that affected outcome>

update:
  confidence_after: 0.0-1.0
  confidence_change: +X.XX or -X.XX
  status_change: none | confirmed | adjusted | invalidated
  methodology_adjustment: <did this reveal a flaw in the approach?>

lessons:
  what_worked: <what was correct>
  what_didnt: <what was wrong>
  pattern_recognized: <does this resemble a known pattern?>
  reusable_insight: <what can be applied to future situations?>

memory_updates:
  affected_memories:
    - memory_id: <id>
      action: confidence_adjusted | promoted | demoted | archived
      reason: <why>
  neo4j_updates:
    - node_id: <id>
      relationship: GENERATED | UPDATED
```

## 4. Feedback Result Types

| Result | Meaning | Typical Confidence Change |
|--------|---------|--------------------------|
| **CONFIRMED** | Outcome matched expectation closely | +0.05 to +0.15 |
| **PARTIALLY_CONFIRMED** | Direction right, magnitude/details off | -0.05 to +0.05 |
| **INCONCLUSIVE** | Not enough data to judge | 0 (extend checkpoint) |
| **CONTRADICTED** | Outcome opposite of expectation | -0.15 to -0.30 |
| **INVALIDATED** | Expectation fundamentally wrong | -0.30+ (archive) |

## 5. AMS Integration

When feedback is recorded, AMS re-evaluates the linked memories:

### Confirmed
- Confidence: +0.10 first confirmation, +0.05 each additional (diminishing)
- Stability: +0.15
- 3+ confirmations with stability ≥ 0.60 → promote to long_term
- 5+ confirmations with stability ≥ 0.85 → core candidate

### Contradicted/Invalidated
- Confidence: -0.20 first contradiction, -0.15 each additional
- Stability: -0.25 (proven unstable)
- 2+ contradictions → archive with invalidation reason
- Trace the causal chain: WHAT assumption was wrong?

### Inconclusive
- Confidence unchanged, stability unchanged
- Extend checkpoint TTL
- Review: was the checkpoint too early? Wrong metrics?

## 6. Methodology Refinement

When multiple feedback records in the same domain show the same failure pattern:

1. **Diagnose**: Are multiple hypotheses failing for the same reason?
2. **Identify**: Is a specific assumption or method consistently misleading?
3. **Update**: Revise the methodology in the relevant fact_store or skill
4. **Record**: Log the methodology change as a system event

## 7. Domain Extensions

Domain-specific feedback schemas extend this base schema. See:
- `memory/feedback-loop-investment.md` — Investment analysis domain extension

To add a new domain extension:
1. Copy the base schema
2. Add domain-specific fields (e.g., investment adds: `ticker`, `position_size`, `market_context`)
3. Add domain-specific scoring rules
4. Reference this file as the base: `extends: memory/feedback-loop.md`
