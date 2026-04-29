# Cypher Query Templates — Hermes Investment Analysis

## 1. Timeline Reconstruction

### 1.1 Event Timeline for an Entity
Get all events about a company, ordered by time.

```cypher
MATCH (e:Event)-[:ABOUT]->(entity:Entity {ticker: $ticker})
RETURN e.title, e.description, e.timestamp, e.type, e.importance
ORDER BY e.timestamp DESC
LIMIT 50
```

### 1.2 Timeline with Causal Chains
Get events with their causal predecessors.

```cypher
MATCH (e:Event)-[:ABOUT]->(entity:Entity {ticker: $ticker})
OPTIONAL MATCH (cause:Event)-[:CAUSED_BY*1..3]->(e)
RETURN e, cause
ORDER BY e.timestamp DESC
```

### 1.3 Full Entity Timeline (Events + Theses + Decisions + Feedback)
Complete history for an entity.

```cypher
MATCH (e:Event)-[:ABOUT]->(entity:Entity {ticker: $ticker})
OPTIONAL MATCH (t:Thesis)-[:ABOUT]->(entity)
OPTIONAL MATCH (d:Decision)-[:ABOUT]->(entity)
OPTIONAL MATCH (f:Feedback)-[:ABOUT]->(entity)
RETURN
    {type: 'event', data: e, time: e.timestamp},
    {type: 'thesis', data: t, time: t.created},
    {type: 'decision', data: d, time: d.timestamp},
    {type: 'feedback', data: f, time: f.timestamp}
ORDER BY time DESC
```

---

## 2. Causal Chain Tracing

### 2.1 What Caused This Event?
Trace back the causal chain from an event.

```cypher
MATCH path = (cause:Event)-[:CAUSED_BY*1..5]->(target:Event {id: $event_id})
RETURN path
ORDER BY length(path)
```

### 2.2 What Did This Event Cause?
Trace forward the consequences.

```cypher
MATCH path = (source:Event {id: $event_id})-[:CAUSED_BY*1..5]->(effect:Event)
RETURN path
ORDER BY length(path)
```

### 2.3 Causal Path Between Two Events
Find if and how event A led to event B.

```cypher
MATCH path = shortestPath((a:Event {id: $event_a_id})-[:CAUSED_BY*..10]->(b:Event {id: $event_b_id}))
RETURN path
```

---

## 3. Thesis Evolution

### 3.1 Thesis History
How has a thesis changed over time?

```cypher
MATCH (t:Thesis {id: $thesis_id})
OPTIONAL MATCH (t)-[:EVOLVED_FROM*]->(ancestor:Thesis)
OPTIONAL MATCH (descendant:Thesis)-[:EVOLVED_FROM*]->(t)
RETURN t, ancestor, descendant
```

### 3.2 Thesis Confidence Timeline
How has confidence changed?

```cypher
MATCH (t:Thesis {id: $thesis_id})
MATCH (f:Feedback)-[:UPDATED]->(t)
RETURN t.title, t.confidence AS current_confidence,
       f.timestamp, f.confidence_before, f.confidence_after,
       f.type, f.impact
ORDER BY f.timestamp ASC
```

### 3.3 Evidence For and Against a Thesis
All supporting and contradicting evidence.

```cypher
MATCH (t:Thesis {id: $thesis_id})
OPTIONAL MATCH (e:Event)-[:SUPPORTS]->(t)
OPTIONAL MATCH (c:Event)-[:CONTRADICTS]->(t)
RETURN t.title AS thesis,
       collect(DISTINCT {type: 'support', event: e.title, strength: e.strength}) AS supporting,
       collect(DISTINCT {type: 'contradict', event: c.title, strength: c.strength}) AS contradicting
```

### 3.4 Active Theses Sorted by Confidence
Which theses are currently active and need monitoring?

```cypher
MATCH (t:Thesis)
WHERE t.status IN ['active', 'confirmed']
RETURN t.title, t.confidence, t.type, t.created, t.expires
ORDER BY t.confidence DESC
```

### 3.5 Theses Due for Re-evaluation
Which theses have expired or are about to?

```cypher
MATCH (t:Thesis)
WHERE t.status = 'active' AND t.expires < datetime() + duration({days: 7})
RETURN t.title, t.confidence, t.expires
ORDER BY t.expires ASC
```

---

## 4. Feedback Impact Analysis

### 4.1 Feedback Effectiveness
How often does feedback actually change thesis confidence?

```cypher
MATCH (f:Feedback)-[:UPDATED]->(t:Thesis)
RETURN f.type AS feedback_type,
       count(*) AS occurrences,
       avg(abs(f.confidence_after - f.confidence_before)) AS avg_confidence_change,
       collect(t.title)[..5] AS examples
ORDER BY avg_confidence_change DESC
```

### 4.2 Most Invalidated Theses
Which theses have been most contradicted by reality?

```cypher
MATCH (f:Feedback {impact: 'invalidating'})-[:UPDATED]->(t:Thesis)
RETURN t.title, t.type, count(f) AS invalidations, t.status
ORDER BY invalidations DESC
```

### 4.3 Feedback Loop Completeness
Are there theses with no feedback records?

```cypher
MATCH (t:Thesis)
WHERE t.status IN ['active', 'confirmed'] AND t.created < datetime() - duration({days: 90})
  AND NOT EXISTS {
    MATCH (f:Feedback)-[:UPDATED]->(t)
  }
RETURN t.title, t.created, t.confidence
ORDER BY t.created ASC
```

---

## 5. Decision Trace

### 5.1 Decision History for an Entity
All decisions made about a company.

```cypher
MATCH (d:Decision)-[:ABOUT]->(entity:Entity {ticker: $ticker})
OPTIONAL MATCH (t:Thesis)-[:LED_TO]->(d)
RETURN d.timestamp, d.type, d.description, d.rationale, d.outcome, t.title AS based_on_thesis
ORDER BY d.timestamp DESC
```

### 5.2 Decisions Without Outcome Tracking
Decisions that need follow-up.

```cypher
MATCH (d:Decision)
WHERE d.outcome IS NULL AND d.timestamp < datetime() - duration({days: 30})
RETURN d.timestamp, d.type, d.description, d.rationale
ORDER BY d.timestamp ASC
```

### 5.3 Decision Outcome Analysis
What types of decisions work best?

```cypher
MATCH (d:Decision)
WHERE d.outcome IS NOT NULL
RETURN d.type,
       count(*) AS total,
       sum(CASE WHEN d.outcome CONTAINS 'positive' OR d.outcome CONTAINS 'success' THEN 1 ELSE 0 END) AS successes,
       sum(CASE WHEN d.outcome CONTAINS 'negative' OR d.outcome CONTAINS 'failure' THEN 1 ELSE 0 END) AS failures
ORDER BY total DESC
```

---

## 6. Cross-Entity Analysis

### 6.1 Entities with Shared Events
Which companies are connected through common events?

```cypher
MATCH (e1:Entity)<-[:ABOUT]-(event:Event)-[:ABOUT]->(e2:Entity)
WHERE e1.id < e2.id
RETURN e1.name, e2.name, count(event) AS shared_events, collect(event.title)[..5] AS examples
ORDER BY shared_events DESC
```

### 6.2 Indicator → Entity Mapping
Which indicators are most relevant to which entities?

```cypher
MATCH (i:Indicator)-[:ABOUT]->(e:Entity)
RETURN i.name AS indicator, i.category, collect(e.name) AS relevant_entities
ORDER BY i.category, i.name
```

---

## 7. Query Usage Guidelines

1. Parameterize all queries — never string-concatenate user input into Cypher
2. Use `LIMIT` on all timeline queries to prevent unbounded results
3. For large graphs, add date range filters to timeline queries
4. The `CAUSED_BY` chain queries can be expensive — prefer `shortestPath()` for exploration
