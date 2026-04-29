# Timeline Index — Structure

## Purpose
The timeline index stores time-ordered event records for chronological retrieval. It is optimized for queries like:
- "What happened in Q4 2025?"
- "Show me the sequence of events leading up to X"
- "What changed between March and June?"

The timeline index works alongside Neo4j — the index provides fast time-range scans; Neo4j provides relationship and causal chain queries.

## Directory Structure
```
timeline_index/
├── README.md                  # This file
├── timeline_config.yaml       # Index configuration
├── yearly/                    # Events organized by year
│   ├── 2025/
│   └── 2026/
└── snapshots/                 # Periodic index snapshots
```

## Event Organization

Events are stored in yearly directories, one file per month:

```
yearly/2026/04.yaml
```

Each file contains an array of events in chronological order.

## Event Format

```yaml
- event_id: event_20260428_001
  type: earnings
  title: "NVDA Q1 FY2027 Earnings"
  description: "Revenue beat by 5%, guidance raised"
  timestamp: 2026-04-28T14:30:00Z
  importance: 0.85
  entities:
    - entity_nvda
  related_theses:
    - thesis_20260428_ai_chip_demand
  related_events:
    - event_20260415_amd_warning  # PRECEDES
  tags:
    - earnings
    - semiconductor
    - ai
  source: Company 8-K Filing
  recorded_by: agent_hermes
  neo4j_node_id: "<uuid>"
```

## Timeline Configuration

```yaml
# timeline_config.yaml
timeline_index:
  organization: yearly/monthly
  event_format: yaml
  max_events_per_file: 1000
  indexing:
    automatic: true
    on_new_event: true
  search:
    default_range: 90d
    max_range: 3650d
  maintenance:
    archive_after_days: 730  # 2 years
    compress_yearly: true
```

## Query Patterns

### Time Range Query
"Events in Q1 2026"
→ Read `yearly/2026/01.yaml`, `02.yaml`, `03.yaml`
→ Filter by criteria within the files

### Entity Timeline
"All events about NVDA"
→ Scan files within time range
→ Filter by `entities` containing `entity_nvda`

### Event Sequence
"What led to the April sell-off?"
→ Start from target event, trace backward through `related_events`
→ Cross-reference with Neo4j for causal relationships
