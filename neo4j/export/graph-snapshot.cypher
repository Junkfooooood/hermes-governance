// Hermes Memory Graph — Schema Creation Script
// Run: cypher-shell -f graph-snapshot.cypher
// Or paste into Neo4j Browser

// ============================================================================
// Constraints (run before data insertion)
// ============================================================================

CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT thesis_id IF NOT EXISTS FOR (t:Thesis) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT feedback_id IF NOT EXISTS FOR (f:Feedback) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT indicator_id IF NOT EXISTS FOR (i:Indicator) REQUIRE i.id IS UNIQUE;

// ============================================================================
// Indexes (run after constraints)
// ============================================================================

CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX event_type IF NOT EXISTS FOR (e:Event) ON (e.type);
CREATE INDEX thesis_status IF NOT EXISTS FOR (t:Thesis) ON (t.status);
CREATE INDEX thesis_confidence IF NOT EXISTS FOR (t:Thesis) ON (t.confidence);
CREATE INDEX decision_timestamp IF NOT EXISTS FOR (d:Decision) ON (d.timestamp);
CREATE INDEX feedback_timestamp IF NOT EXISTS FOR (f:Feedback) ON (f.timestamp);
CREATE INDEX feedback_impact IF NOT EXISTS FOR (f:Feedback) ON (f.impact);
CREATE INDEX indicator_category IF NOT EXISTS FOR (i:Indicator) ON (i.category);

// ============================================================================
// Sample data — Investment Analysis Example
// Uncomment and customize to bootstrap a tracking graph
// ============================================================================

// -- Entities --
// CREATE (:Entity {id: 'entity_aapl', type: 'company', name: 'Apple Inc.', ticker: 'AAPL', description: 'Consumer electronics and services', created: datetime()});
// CREATE (:Entity {id: 'entity_nvda', type: 'company', name: 'NVIDIA Corp.', ticker: 'NVDA', description: 'GPU and AI accelerator company', created: datetime()});
// CREATE (:Entity {id: 'entity_semiconductor', type: 'sector', name: 'Semiconductor Industry', description: 'Chip design, manufacturing, and equipment', created: datetime()});

// -- Indicator --
// CREATE (:Indicator {id: 'indicator_semi_rev', name: 'Global Semiconductor Revenue', category: 'sector', frequency: 'monthly', fact_pointer: 'fact_store/finance/market_indicators.md'});

// -- Event --
// CREATE (:Event {id: 'event_20260428_nvda_earnings', type: 'earnings', title: 'NVDA Q1 FY2027 Earnings', description: 'Revenue beat by 5%, guidance raised', timestamp: datetime('2026-04-28T00:00:00Z'), importance: 0.85, source: 'Company 8-K Filing'});

// -- Thesis --
// CREATE (:Thesis {id: 'thesis_20260428_ai_chip_demand', type: 'bullish', title: 'AI Chip Demand Structural Growth', summary: 'AI infrastructure buildout is in early innings; semiconductor demand has multi-year runway', confidence: 0.80, status: 'active', created: datetime(), expires: datetime() + duration({days: 90})});

// -- Relationships --
// MATCH (e:Event {id: 'event_20260428_nvda_earnings'}), (t:Thesis {id: 'thesis_20260428_ai_chip_demand'})
// CREATE (e)-[:SUPPORTS {strength: 0.80, note: 'Data center revenue grew 40% YoY'}]->(t);

// MATCH (e:Event {id: 'event_20260428_nvda_earnings'}), (ent:Entity {id: 'entity_nvda'})
// CREATE (e)-[:ABOUT]->(ent);

// MATCH (t:Thesis {id: 'thesis_20260428_ai_chip_demand'}), (ent:Entity {id: 'entity_semiconductor'})
// CREATE (t)-[:ABOUT]->(ent);
