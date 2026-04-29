# Skill Merge Log

Records all skill merge decisions. Each entry is immutable — append only.

---

## Merge Records

| Merge ID | Date | Merged Skill | Merged Into | Reason | Overlap | Decided By |
|----------|------|-------------|-------------|--------|---------|------------|
| — | — | — | — | — | — | — |

*No merge records yet. Entries will be logged here as skill overlaps are detected and resolved.*

---

## Merge Decision Template

```yaml
merge_id: merge_<YYYYMMDD>_<seq>
date: <ISO8601>
merged_skill: skills/<category>/<skill_name>
merged_into: skills/<category>/<canonical_skill_name>
reason: overlap | special_case | superseded
overlap_ratio: 0.XX
canonical_score: 0.XX
merged_score: 0.XX
details: <narrative explanation>
decided_by: <agent_id>
reviewed_by: <human or agent>
```
