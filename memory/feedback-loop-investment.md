---
extends: memory/feedback-loop.md
domain: finance
description: Domain extension of the generic feedback loop for investment analysis. Adds investment-specific fields (ticker, position_size, market_context) on top of the base schema.
---

# Investment Feedback Loop v1

> **Domain Extension** — This file extends the generic [`feedback-loop.md`](feedback-loop.md) base schema. The base schema defines the universal feedback cycle (hypothesis → action → observe → compare → update → record). This file adds investment-specific fields and scoring rules.

## 1. Purpose

The investment feedback loop is the mechanism by which Hermes learns from real-world market outcomes. It closes the gap between analysis and reality: thesis → action → market outcome → thesis update → methodology improvement.

This is the implementation of Law 6 (Learning from Reality) for the investment analysis domain.

## 2. The Investment Feedback Cycle

```
┌──────────────────────┐
│  1. FORM THESIS      │  ← Record: thesis, expected outcome, confidence, basis
│     (Neo4j node)     │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  2. DEFINE CHECKPOINT│  ← When to re-evaluate? What data to check?
│     (timeline event) │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  3. TAKE ACTION      │  ← Optional: buy/sell/hold decision (Neo4j Decision node)
│     (decision node)  │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  4. OBSERVE OUTCOME  │  ← At checkpoint: collect real-world data
│     (event node)     │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  5. COMPARE          │  ← Expected vs. Actual → gap analysis
│     (feedback node)  │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  6. UPDATE           │  ← Adjust confidence, promote/demote, refine methodology
│     (AMS + Neo4j)    │
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  7. RECORD           │  ← Write feedback record, update memory weights
│     (archive + log)  │
└──────────────────────┘
```

## 3. Thesis Feedback Record

```yaml
---
feedback_id: fb_<YYYYMMDD>_<seq>
type: investment_feedback
related_thesis_id: thesis_<id>
related_event_ids: [event_<id>, ...]
related_decision_id: decision_<id>  # if action was taken
timestamp: <ISO8601>
neo4j_feedback_node: <uuid>
---

thesis:
  statement: <the original thesis>
  confidence_before: 0.0-1.0
  expected_outcome: <what was predicted to happen>
  expected_timeline: <when was it expected>

checkpoint:
  type: earnings | macro_data | price_target | time_elapsed | event_trigger
  description: <what triggered the re-evaluation>

actual_outcome:
  result: CONFIRMED | PARTIALLY_CONFIRMED | INCONCLUSIVE | CONTRADICTED | INVALIDATED
  data_points:
    - metric: <what was measured>
      expected: <value>
      actual: <value>
      delta: <difference>
  narrative: <qualitative description of what happened>

gap_analysis:
  gap_type: no_gap | minor_deviation | significant_deviation | complete_miss
  root_cause: <why did expected and actual diverge?>
  was_thesis_wrong: true | false
  was_timing_wrong: true | false
  was_magnitude_wrong: true | false
  external_factor: <was there an unforeseeable event?>

update:
  confidence_after: 0.0-1.0
  confidence_change: +X.XX or -X.XX
  thesis_status: active | confirmed | adjusted | invalidated
  methodology_adjustment: <did this reveal a flaw in the analysis method?>
  promoted_to_long_term: true | false
  next_checkpoint: <ISO8601 or null if thesis closed>

lessons:
  what_worked: <what part of the analysis was correct>
  what_didnt: <what part was wrong>
  pattern_recognized: <does this resemble a known pattern?>
  methodology_update: <should the analysis framework be adjusted?>

memory_updates:
  affected_memories:
    - memory_id: <id>
      action: confidence_adjusted | demoted | promoted
      reason: <why>
```

## 4. Feedback Scoring for AMS Integration

When feedback is recorded, AMS re-evaluates the affected memories:

### Thesis Confirmed (+ feedback)
- Confidence increase: +0.10 for first confirmation, +0.05 for each additional (diminishing returns)
- Stability increase: +0.15
- After 3+ confirmations → promote thesis to long_term
- After 5+ confirmations with stability ≥ 0.85 → core candidate

### Thesis Contradicted (- feedback)
- Confidence decrease: -0.20 for first contradiction, -0.15 for each additional
- Stability decrease: -0.25 (the thesis was proven unstable)
- After 2+ contradictions → archive thesis with invalidation reason
- Trace causal chain: WHAT assumption was wrong?

### Thesis Inconclusive (neutral feedback)
- Confidence unchanged
- Stability unchanged
- Extend TTL for another checkpoint cycle
- Review: was the checkpoint too early? Wrong metrics?

## 5. Methodology Refinement from Feedback

When multiple theses in the same domain fail in the same way, it indicates a methodology problem:

### Diagnosis Questions
1. Are multiple theses failing for the same reason? → Methodology flaw
2. Is a specific indicator consistently misleading? → Downgrade indicator reliability
3. Is a pattern failing to repeat? → Pattern may be overfitted to historical data
4. Are external factors systematically missed? → Add factors to analysis framework

### Methodology Update Actions
- Downgrade indicator: reduce its weight in the AMS scoring for related theses
- Deprecate pattern: move to `fact_store/patterns/` with deprecation note
- Update framework: revise `fact_store/finance/valuation_principles.md` with lessons learned
- Add to skills: if a new analysis technique emerged from the feedback

## 6. Feedback Review Schedule

| Feedback Age | Review Action |
|-------------|---------------|
| At recording | Immediate: update thesis confidence + Neo4j graph |
| 30 days | Check: has the thesis been re-tested? If not, flag for checkpoint |
| 90 days | Aggregate: what patterns emerge from multiple feedback records? |
| 365 days | Archive: move feedback to archive, keep Neo4j node |

## 7. Feedback-Driven Learning Loop (Automated)

AMS periodically runs this analysis:

```
1. Query all feedback records from last 90 days
2. Group by thesis type, sector, and methodology used
3. Calculate:
   - Confirmation rate: confirmed / total theses
   - Average confidence change: mean(confidence_after - confidence_before)
   - Methodology accuracy: confirmation rate per analysis method
4. Flag:
   - Methodology with <40% confirmation rate → review and update
   - Sector with declining confirmation rate → sector thesis may need revision
   - Agent consistently overconfident (confidence_before >> actual outcome) → recalibrate scoring
5. Report findings to coordinator for methodology refinement
```

## 8. Cross-System Integration

| System | Role in Feedback Loop |
|--------|----------------------|
| **Neo4j** | Nodes: Thesis → Decision → Feedback. Edges: BASED_ON, LED_TO, GENERATED, UPDATED |
| **AMS** | Re-scores affected memories; triggers promotion/demotion |
| **Qdrant** | Semantic search for similar past feedback patterns |
| **fact_store** | Stores updated methodologies and frameworks |
| **byterover events** | Timeline records of thesis checkpoints and feedback events |
| **skills governance** | Deprecates or updates skills that consistently underperform |

## 9. Example: Complete Feedback Record

```yaml
---
feedback_id: fb_20260515_001
type: investment_feedback
related_thesis_id: thesis_20260428_ai_chip_demand
related_event_ids: [event_20260515_nvda_earnings]
related_decision_id: null  # no action taken, tracking only
timestamp: 2026-05-15T20:30:00Z
---

thesis:
  statement: "AI infrastructure buildout is in early innings; semiconductor demand has multi-year runway"
  confidence_before: 0.80
  expected_outcome: "NVDA data center revenue growth ≥ 30% YoY; guidance raise"
  expected_timeline: "Q1 FY2027 earnings, ~May 15 2026"

actual_outcome:
  result: CONFIRMED
  data_points:
    - metric: "Data center revenue YoY growth"
      expected: "≥ 30%"
      actual: "42%"
      delta: "+12pp above expectation"
    - metric: "Next quarter guidance"
      expected: "Raise"
      actual: "Raised by 8%"
      delta: "above expectation"

gap_analysis:
  gap_type: no_gap
  root_cause: null
  was_thesis_wrong: false
  was_timing_wrong: false
  was_magnitude_wrong: false  # growth was even stronger than expected
  external_factor: null

update:
  confidence_after: 0.85
  confidence_change: +0.05
  thesis_status: active
  methodology_adjustment: null
  promoted_to_long_term: false  # already long-term
  next_checkpoint: 2026-08-15T00:00:00Z  # next earnings

lessons:
  what_worked: "Data center CapEx trend correctly identified as leading indicator"
  what_didnt: null  # nothing failed in this case
  pattern_recognized: "Cloud provider CapEx → chip demand with 1-2 quarter lag"
  methodology_update: null

memory_updates:
  affected_memories:
    - memory_id: ltm_20260428_001
      action: confidence_adjusted
      reason: "Real-world data confirmed thesis prediction"
```
