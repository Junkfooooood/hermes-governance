# Neo4j Graph Schema — Hermes Memory Graph v1

## 1. Purpose

The Neo4j graph layer stores relationships, causality chains, and time-ordered facts. It is the engine for:
- **Timeline reconstruction**: What happened and when?
- **Causal chain tracing**: Why did X happen? What led to Y?
- **Thesis evolution**: How has a view changed over time?
- **Feedback impact**: What effect did feedback have on related theses?

## 2. Node Types

### 2.1 Entity
Represents a company, person, asset, sector, or any real-world entity being tracked.

```cypher
CREATE (e:Entity {
    id: 'string',               // Unique: entity_<name_slug>
    type: 'company | person | asset | sector | index | country',
    name: 'string',             // Display name
    ticker: 'string',           // Optional: stock ticker
    description: 'string',      // Brief description
    created: datetime(),
    updated: datetime()
})
```

### 2.2 Event
Represents something that happened at a specific time.

```cypher
CREATE (e:Event {
    id: 'string',               // Unique: event_<YYYYMMDD>_<slug>
    type: 'earnings | macro_data | policy_change | news | market_move | feedback',
    title: 'string',            // Short description
    description: 'string',      // Longer description
    timestamp: datetime(),       // When it occurred
    importance: 0.0-1.0,
    source: 'string',           // Data source
    recorded: datetime()         // When this event was recorded
})
```

### 2.3 Thesis
Represents an investment thesis or analytical conclusion.

```cypher
CREATE (t:Thesis {
    id: 'string',               // Unique: thesis_<YYYYMMDD>_<slug>
    type: 'bullish | bearish | neutral | observation',
    title: 'string',
    summary: 'string',
    confidence: 0.0-1.0,        // Current confidence level
    status: 'active | confirmed | invalidated | superseded | archived',
    created: datetime(),
    updated: datetime(),
    expires: datetime(),        // Optional: when to re-evaluate
    memory_pointer: 'string'    // Path to full analysis document
})
```

### 2.4 Decision
Represents an action taken based on a thesis.

```cypher
CREATE (d:Decision {
    id: 'string',               // Unique: decision_<YYYYMMDD>_<slug>
    type: 'buy | sell | hold | rebalance | research_deeper | wait',
    description: 'string',
    timestamp: datetime(),
    rationale: 'string',
    outcome: 'string',          // Fill in later: what happened
    outcome_recorded: datetime()
})
```

### 2.5 Feedback
Represents a real-world validation or invalidation.

```cypher
CREATE (f:Feedback {
    id: 'string',               // Unique: fb_<YYYYMMDD>_<seq>
    type: 'confirmation | contradiction | partial_match | new_information',
    description: 'string',
    timestamp: datetime(),
    expected: 'string',         // What the thesis predicted
    actual: 'string',           // What actually happened
    gap_analysis: 'string',     // Why the difference
    impact: 'none | minor | significant | invalidating',
    memory_pointer: 'string'    // Path to full feedback record
})
```

### 2.6 Indicator
Represents a tracked metric or signal.

```cypher
CREATE (i:Indicator {
    id: 'string',               // Unique: indicator_<slug>
    name: 'string',             // e.g., "US ISM Manufacturing PMI"
    category: 'macro | market | sector | sentiment',
    frequency: 'daily | weekly | monthly | quarterly',
    current_value: 'string',    // Latest reading
    current_timestamp: datetime(),
    trend: 'rising | falling | flat',
    fact_pointer: 'string'      // Path to indicator reference doc
})
```

## 3. Relationship Types

### 3.1 CAUSED_BY (Event → Event)
Causal chain: "X happened because Y happened."

```cypher
(:Event)-[:CAUSED_BY {
    confidence: 0.0-1.0,
    reasoning: 'string'
}]->(:Event)
```

### 3.2 SUPPORTS (Event → Thesis) / CONTRADICTS (Event → Thesis)
Evidence for or against a thesis.

```cypher
(:Event)-[:SUPPORTS {
    strength: 0.0-1.0,
    note: 'string'
}]->(:Thesis)

(:Event)-[:CONTRADICTS {
    strength: 0.0-1.0,
    note: 'string'
}]->(:Thesis)
```

### 3.3 PRECEDES (Event → Event)
Temporal ordering without claimed causality.

```cypher
(:Event)-[:PRECEDES {
    gap_days: integer
}]->(:Event)
```

### 3.4 EVOLVED_FROM (Thesis → Thesis)
Thesis refinement over time.

```cypher
(:Thesis)-[:EVOLVED_FROM {
    reason: 'refined | contradicted | expanded | narrowed',
    date: datetime()
}]->(:Thesis)
```

### 3.5 BASED_ON (Thesis → Thesis | Thesis → Event)
The intellectual foundation of a thesis.

```cypher
(:Thesis)-[:BASED_ON {
    weight: 0.0-1.0
}]->(:Thesis)

(:Thesis)-[:BASED_ON {
    weight: 0.0-1.0
}]->(:Event)
```

### 3.6 LED_TO (Decision → Decision | Thesis → Decision)
Decision-making trace.

```cypher
(:Thesis)-[:LED_TO {
    confidence_at_time: 0.0-1.0
}]->(:Decision)

(:Decision)-[:LED_TO {
    reason: 'string'
}]->(:Decision)
```

### 3.7 ABOUT (Any → Entity)
What entity is this about?

```cypher
(:Event|Thesis|Decision|Indicator)-[:ABOUT]->(:Entity)
```

### 3.8 GENERATED (Decision | Thesis → Feedback)
Decision or thesis produced real-world feedback.

```cypher
(:Decision|Thesis)-[:GENERATED]->(:Feedback)
```

### 3.9 UPDATED (Feedback → Thesis)
Feedback changed a thesis's confidence.

```cypher
(:Feedback)-[:UPDATED {
    confidence_before: 0.0-1.0,
    confidence_after: 0.0-1.0,
    direction: 'increased | decreased | unchanged'
}]->(:Thesis)
```

---

## 4. Graph Constraints & Indexes

```cypher
// Uniqueness constraints
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT thesis_id IF NOT EXISTS FOR (t:Thesis) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT feedback_id IF NOT EXISTS FOR (f:Feedback) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT indicator_id IF NOT EXISTS FOR (i:Indicator) REQUIRE i.id IS UNIQUE;

// Performance indexes for common queries
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.type);
CREATE INDEX thesis_status IF NOT EXISTS FOR (t:Thesis) ON (t.status);
CREATE INDEX thesis_confidence IF NOT EXISTS FOR (t:Thesis) ON (t.confidence);
CREATE INDEX feedback_impact IF NOT EXISTS FOR (f:Feedback) ON (f.impact);
CREATE INDEX indicator_category IF NOT EXISTS FOR (i:Indicator) ON (i.category);
```

---

## 5. Data Freshness

- Event nodes: retain indefinitely (historical record)
- Thesis nodes: retain indefinitely; archive when status = `archived`
- Decision nodes: retain indefinitely (audit trail)
- Feedback nodes: retain permanently (learning record)
- Indicator values: retain latest 24 months of data points; archive older
