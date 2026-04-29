# Event Record Schema — Investment Analysis

## Purpose

Every significant event in the investment analysis workflow is recorded as a structured event. Events form the backbone of the timeline index and feed into Neo4j's causal graph.

## Event Schema

```yaml
---
event_id: event_<YYYYMMDD>_<seq>
type: <event_type>
title: <one-line description>
description: <2-5 sentence narrative>
timestamp: <ISO8601>
recorded_at: <ISO8601 — when this was written>
importance: 0.0-1.0
confidence: 0.0-1.0  # How certain is this event record?
source: <where the information came from>
source_url: <URL if applicable>
entities:
  - <entity_id>
related_theses:
  - <thesis_id>
related_events:
  - event_id: <id>
    relationship: PRECEDES | CAUSED_BY | CONTRADICTS | SUPPORTS
tags:
  - <tag>
neo4j_node_id: <uuid after graph insertion>
pointer: <path to full analysis or related memory>
---

## Event Narrative

<Detailed description, context, and implications.>
```

## Event Types

| Type | Description | Example |
|------|-------------|---------|
| `earnings` | Company earnings report | Quarterly results, guidance changes |
| `macro_data` | Macroeconomic data release | GDP, CPI, employment, PMI |
| `policy_change` | Monetary or fiscal policy change | Fed rate decision, tax law change |
| `news` | Significant news event | M&A announcement, regulatory action |
| `market_move` | Notable market price action | >5% single-day move with identifiable catalyst |
| `thesis_update` | Significant change to a thesis | Confidence adjustment, status change |
| `decision` | Investment decision made | Buy/sell, allocation change |
| `feedback` | Real-world validation of a thesis | Earnings confirming/contradicting model |
| `research_milestone` | Research project checkpoint | Draft complete, key finding |
| `system_event` | Hermes internal system event | Memory promotion, skill deprecation |

## Event Recording Rules

1. **Record at the time of occurrence, not retroactively.** Timestamp reflects when the event happened, not when it was written down.
2. **One event = one thing.** Don't bundle "NVDA beat earnings AND Fed raised rates" into one event.
3. **Always link to entities and theses.** An unlinked event is a dead end in the graph.
4. **Record source.** Every event must be traceable to its source.
5. **Separate fact from interpretation.** The event record is factual. Put interpretation in linked theses or feedback records.

## Event Lifecycle

```
Event occurs → Recorded in timeline_index → Inserted in Neo4j → 
  Embedded for Qdrant semantic search → Available for timeline queries
```

Events are immutable once recorded. Corrections create a new event of type `correction` linked to the original via `CONTRADICTS`.
