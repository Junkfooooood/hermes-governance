# Archive Memory Layer

## Purpose
Store deprecated, superseded, expired, and merged content. Archives preserve audit trails and enable historical lookup. Archived memories are excluded from default recall but queryable when explicitly requested.

## Archive Reason Codes

| Code | Meaning | Example |
|------|---------|---------|
| `TTL_EXPIRED` | Time-to-live expired without renewal | Short-term observation past its window |
| `SUPERSEDED` | Replaced by a newer, more accurate memory | Old thesis replaced by updated analysis |
| `INVALIDATED` | Proven wrong by real-world feedback | Thesis contradicted by market data |
| `MERGED` | Content absorbed into another memory | Duplicate entries consolidated |
| `DEPRECATED` | Explicitly marked as no longer relevant | Old methodology no longer used |
| `TASK_COMPLETE` | Task finished, no follow-up needed | One-shot analysis delivered |

## Entry Template

```markdown
---
id: arc_<YYYYMMDD>_<seq>
type: <original_type>
layer: archived
original_layer: <core | long_term | short_term>
archived: <ISO8601>
reason: <archive_reason_code>
superseded_by: <pointer to replacement, if applicable>
retain_until: <ISO8601 — default +365 days>
---

## <Original Title>

### Original Content Summary
<Brief summary of what this memory contained>

### Archive Reason
<Why this was archived>

### Recovery Path
<How to find this if needed again: Neo4j node ID, Qdrant vector ID, file path>
```

## Retention Policy
- All archived memories: retain minimum 365 days from archival date
- Safety incidents and feedback records: retain permanently
- Graph nodes (Neo4j): retain indefinitely (relationships remain valuable even when facts change)
- After retention period: eligible for permanent deletion (manual review required)

## Recovery
Archived memories can be recovered (moved back to an active layer) if:
- New evidence supports the archived conclusion
- The superseding memory is itself invalidated
- Explicit user request

Recovery requires AMS re-scoring before re-promotion.
