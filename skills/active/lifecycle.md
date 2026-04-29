# Skill Lifecycle — Automation Rules

## States
- active
- low_frequency
- deprecated
- merged

## Scoring Formula

```
skill_score = usage_freq * 0.40 + success_rate * 0.30 + recency * 0.20 + uniqueness * 0.10
```

## Transition Thresholds

| Transition | Trigger Condition | Automation |
|-----------|-------------------|------------|
| active → low_frequency | `skill_score < 0.50` sustained 30d, OR not invoked in 30d, OR success rate < 50% in last 3 | Semi-auto: flag for review, agent confirms |
| active → deprecated | Superseded by new skill, OR domain irrelevant, OR success rate < 20% over 5+ invocations | Manual: requires agent judgment |
| active → merged | Overlap > 70% with another active skill, AND one is clearly canonical | Semi-auto: recommend merge, agent executes |
| low_frequency → deprecated | Not invoked in 90d, OR `skill_score < 0.30` | Auto: system moves to deprecated |
| low_frequency → active | `skill_score ≥ 0.70`, invoked 3+ times in 14d, no >70% overlap | Semi-auto: flag for re-promotion |
| deprecated → deleted | 365d since deprecation, no historical value | Manual: requires human confirmation |

## Overlap Detection

```
overlap_ratio = tag_jaccard * 0.30 + desc_similarity * 0.50 + tool_jaccard * 0.20
```
- ≥ 0.70: Strong overlap → merge candidate
- 0.40–0.69: Moderate → review
- < 0.40: Acceptable

## Periodic Review

| State | Interval | Check |
|-------|----------|-------|
| active | 30d | Score, overlap, freshness |
| low_frequency | 60d | Re-promotion eligible? |
| deprecated | 180d | Still worth keeping? |
| merged | 180d | Canonical still active? |

## Merge rules
- Same problem, duplicate behavior, or strict special case → merge into canonical skill.
- Keep a pointer from merged variants to the active skill.

## Deprecation rules
- Rarely used, obsolete, or replaced → move to deprecated.
- Keep the historical record, but exclude from default retrieval.
