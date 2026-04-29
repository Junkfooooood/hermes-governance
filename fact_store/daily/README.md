# Daily Memory Store

## Purpose
Store daily observations, personal notes, life events, and everyday knowledge. This is the most general-purpose fact_store domain — anything that doesn't fit a specific domain goes here.

## What Belongs Here
- Daily observations and reflections
- Personal preferences and habits (discovered, not declared)
- Life events and milestones
- General knowledge facts not tied to a specific domain
- Notes about places, experiences, routines
- Ideas and brainstorming fragments worth keeping

## What Does NOT Belong Here
- Domain-specific knowledge (→ `fact_store/<domain>/`)
- Core identity facts (→ `memory/core/`)
- Validated reusable frameworks (→ `memory/long_term/`)
- Temporary hypotheses (→ `memory/short_term/`)

## Entry Template

```markdown
---
id: daily_<YYYYMMDD>_<seq>
type: observation | note | event | preference | idea
layer: short_term (default) | long_term (if validated)
importance: 0.0-1.0
stability: 0.0-1.0
confidence: 0.0-1.0
status: active
created: <ISO8601>
tags: [<descriptive tags>]
context: <where/when/why this was noted>
---

## <Title>

### Note
<The observation or fact>

### Why It Matters
<Why this is worth remembering>

### Related
- <link to related memories, facts, events>
```

## Examples

### Observation
```markdown
---
id: daily_20260428_001
type: observation
layer: short_term
importance: 0.40
stability: 0.50
confidence: 0.70
status: active
created: 2026-04-28T09:00:00Z
tags: [commute, productivity, routine]
context: Morning routine observation
---

## Morning Commute — Podcast vs. Silence

### Note
Tested doing the morning commute in silence vs. listening to podcasts. Silence led to better focus in the first hour of work. Podcast days started slower.

### Why It Matters
Potential productivity optimization. Worth testing for a week to confirm.

### Related
- None yet — track for 7 days, then decide if this becomes a long_term pattern
```

### Life Event
```markdown
---
id: daily_20260428_002
type: event
layer: long_term
importance: 0.80
stability: 0.90
confidence: 1.00
status: active
created: 2026-04-28T00:00:00Z
tags: [milestone, personal]
context: Personal milestone
---

## <Event Title>

### Note
<Description of the event>

### Why It Matters
<Significance of this event>

### Related
- Neo4j Event node: `<id>`
```
