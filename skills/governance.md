# Skills Governance Engine v1

## 1. Purpose

Skills are executable knowledge — methodologies, workflows, and operational procedures. Like memories, skills have a lifecycle. Unlike memories, skills are about HOW to do things, not WHAT is true.

This governance engine defines:
- How skills are scored for health and relevance
- When skills should be merged, demoted, or deprecated
- The automation rules for skill lifecycle management

## 2. Skill Scoring

Each skill is scored on four dimensions (different from memory scoring because skills are about execution, not truth):

| Dimension | What It Measures | Formula |
|-----------|-----------------|---------|
| **Usage Frequency** | How often is this skill invoked? | `invocations / days_since_creation` (capped at 1.0) |
| **Success Rate** | How often does this skill produce correct results? | `successful_invocations / total_invocations` |
| **Recency** | When was this skill last used? | `1.0 - (days_since_last_use / 90)` clamped to [0,1] |
| **Uniqueness** | How much does this skill overlap with others? | `1.0 - (max_overlap_ratio_with_any_other_skill)` |

### Composite Skill Score

```
skill_score = (
    usage_frequency  * 0.40 +
    success_rate     * 0.30 +
    recency          * 0.20 +
    uniqueness       * 0.10
)
```

### Score Interpretation

| Score Range | Status | Action |
|-------------|--------|--------|
| ≥ 0.70 | Healthy | Keep in active |
| 0.40–0.69 | At Risk | Evaluate for low_frequency |
| < 0.40 | Unhealthy | Evaluate for deprecated or merged |

## 3. Lifecycle States

```
 active  ── low usage ──→  low_frequency  ── stale ──→  deprecated
   │                            │                           │
   │                            │                           │
   ├── overlap ──→ merged       ├── overlap ──→ merged      │
   │                            │                           │
   └── superseded ──→ deprecated│                           │
                                └── superseded ──→ deprecated
```

### 3.1 Active → Low Frequency

**Triggers (ANY):**
- `skill_score < 0.50` for 30+ days
- Not invoked in 30 days
- Success rate < 50% on last 3 invocations

**Action:**
- Move skill directory: `skills/active/<skill>` → `skills/low_frequency/<skill>`
- Update skill metadata: `status: low_frequency`, `demoted_at: <ISO8601>`
- Skill remains queryable but excluded from default prompt injection

### 3.2 Active → Deprecated

**Triggers (ANY):**
- Superseded by a new skill (creator marks as superseded)
- Domain no longer relevant to active objectives
- Fundamentally broken (success rate < 20% over 5+ invocations)

**Action:**
- Move: `skills/active/<skill>` → `skills/deprecated/<skill>`
- Add deprecation reason and replacement pointer to frontmatter
- Excluded from all default retrieval
- Kept for historical reference

### 3.3 Active → Merged

**Triggers (ALL):**
- Overlap ratio > 70% with another active skill
- Both skills serve the same problem domain
- One skill is clearly the canonical version (higher score, better maintained)

**Action:**
- Move subordinate skill: `skills/active/<skill>` → `skills/merged/<skill>`
- Add frontmatter: `merged_into: <canonical_skill_path>`, `merged_at: <ISO8601>`
- Update canonical skill: add `absorbed: [<merged_skill_name>]`
- Record merge decision in `skills/merged/merge-log.md`

### 3.4 Low Frequency → Deprecated

**Triggers (ANY):**
- Not invoked in 90 days
- Superseded by a new active skill
- `skill_score < 0.30`

### 3.5 Low Frequency → Active (Re-promotion)

**Triggers (ALL):**
- `skill_score ≥ 0.70` on re-evaluation
- Invoked at least 3 times in the last 14 days
- No overlap > 70% with an existing active skill

## 4. Overlap Detection

Two skills overlap when they solve the same problem. Overlap is measured by:

1. **Tag overlap**: Jaccard similarity of tags. `|tags_A ∩ tags_B| / |tags_A ∪ tags_B|`
2. **Description similarity**: Cosine similarity of description embeddings
3. **Tool overlap**: Shared tools in skill schema

```
overlap_ratio = (
    tag_jaccard       * 0.30 +
    desc_similarity   * 0.50 +
    tool_jaccard      * 0.20
)
```

### Thresholds
- ≥ 0.70: Strong overlap → merge recommendation
- 0.40–0.69: Moderate overlap → flag for review
- < 0.40: Acceptable overlap

## 5. Periodic Review Schedule

| State | Review Interval | Action |
|-------|----------------|--------|
| Active | 30 days | Re-score; check for overlap with new skills |
| Low Frequency | 60 days | Re-score; evaluate for re-promotion or deprecation |
| Deprecated | 180 days | Check if still worth keeping as historical reference |
| Merged | 180 days | Verify canonical skill still exists and is active |

## 6. Automation Prompts

### Skill Health Report
Agent runs this to assess all active skills:

```
## Skill Health Report — [Date]

For each skill in skills/active/:
1. Score: ___ (using scoring formula)
2. Last invoked: ___
3. Success rate: ___ (last 5 invocations)
4. Overlap with other skills: ___ (max overlap ratio + which skill)
5. Recommendation: keep | demote | merge | deprecate
```

### Merge Decision Record
When merging skills, record:

```yaml
merge_id: merge_<YYYYMMDD>_<seq>
date: <ISO8601>
merged_skill: <name>
merged_into: <canonical_skill_name>
reason: overlap | special_case | superseded
overlap_ratio: <0.0-1.0>
canonical_score: <skill_score>
merged_score: <skill_score>
decided_by: <agent_id>
```

## 7. Integration with AMS

Skills governance operates independently from AMS (memory governance) but follows the same principles:
- Score → Route → Lifecycle Action
- Promotions require evidence; demotions are automatic on threshold breach
- Nothing is deleted — everything is archived/deprecated/merged

Skills that are promoted to core (extremely stable, high-score, fundamental to operation) should have their pointer added to SOUL.md's routing section.
