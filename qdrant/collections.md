# Qdrant Collection Schemas

## Collection: hermes_memories

```json
{
  "collection_name": "hermes_memories",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "optimizers_config": {
    "default_segment_number": 2
  },
  "hnsw_config": {
    "m": 16,
    "ef_construct": 100
  }
}
```

### Payload Indexes
```json
[
  {"field": "memory_id", "field_type": "keyword"},
  {"field": "type", "field_type": "keyword"},
  {"field": "layer", "field_type": "keyword"},
  {"field": "importance", "field_type": "float"},
  {"field": "stability", "field_type": "float"},
  {"field": "confidence", "field_type": "float"},
  {"field": "tags", "field_type": "keyword"},
  {"field": "source", "field_type": "keyword"},
  {"field": "timestamp", "field_type": "datetime"}
]
```

---

## Collection: hermes_facts

```json
{
  "collection_name": "hermes_facts",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

### Payload Indexes
```json
[
  {"field": "fact_id", "field_type": "keyword"},
  {"field": "category", "field_type": "keyword"},
  {"field": "subcategory", "field_type": "keyword"},
  {"field": "tags", "field_type": "keyword"},
  {"field": "importance", "field_type": "float"}
]
```

---

## Collection: hermes_events

```json
{
  "collection_name": "hermes_events",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

### Payload Indexes
```json
[
  {"field": "event_id", "field_type": "keyword"},
  {"field": "type", "field_type": "keyword"},
  {"field": "timestamp", "field_type": "datetime"},
  {"field": "importance", "field_type": "float"},
  {"field": "tags", "field_type": "keyword"},
  {"field": "entities", "field_type": "keyword"}
]
```
