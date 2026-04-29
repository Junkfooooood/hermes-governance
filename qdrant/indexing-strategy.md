# Qdrant Indexing Strategy — Hermes Semantic Memory

## 1. Purpose

Qdrant provides vector similarity search for semantic recall. It answers: "I don't remember the exact keywords, but I know what it's about." Use Qdrant when keyword/tag search in fact_store or skills returns insufficient results.

## 2. Embedding Model

### Recommended: text-embedding-3-small (OpenAI)
- Dimensions: 1536
- Cost: ~$0.02 per 1M tokens
- Good balance of quality and cost
- Multilingual support

### Alternatives
- `bge-large-en-v1.5` (self-hosted, 1024 dims)
- `all-MiniLM-L6-v2` (self-hosted, 384 dims, lightweight)

## 3. Collection Design

### Collection 1: `hermes_memories`
Semantic index of all memory summaries.

```json
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

**Payload schema:**
```json
{
  "memory_id": "string",
  "type": "principle | thesis | fact | methodology | observation | hypothesis",
  "layer": "core | long_term | short_term | archived",
  "importance": 0.0-1.0,
  "stability": 0.0-1.0,
  "confidence": 0.0-1.0,
  "tags": ["string array"],
  "source": "conversation | research | feedback | external",
  "timestamp": "ISO8601",
  "pointer": "string — file path to full content",
  "content_summary": "string — 1-2 sentence summary for display",
  "ttl_days": "integer"
}
```

### Collection 2: `hermes_facts`
Semantic index of structured facts from fact_store.

```json
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

**Payload schema:**
```json
{
  "fact_id": "string",
  "category": "finance | people | project | pattern",
  "subcategory": "string",
  "tags": ["string array"],
  "importance": 0.0-1.0,
  "pointer": "string — fact_store path",
  "content_summary": "string"
}
```

### Collection 3: `hermes_events`
Semantic index of time-stamped events for hybrid search.

```json
{
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  }
}
```

**Payload schema:**
```json
{
  "event_id": "string",
  "type": "earnings | macro | news | policy | market_move | feedback",
  "timestamp": "ISO8601",
  "importance": 0.0-1.0,
  "tags": ["string array"],
  "entities": ["entity IDs this event relates to"],
  "pointer": "string — byterover event path or Neo4j node ID",
  "content_summary": "string"
}
```

## 4. Indexing Strategy

### What Gets Indexed in Qdrant

| Source | What | When |
|--------|------|------|
| mem0 extraction | Every extracted memory summary | On session end, after AMS scoring |
| fact_store entries | Summary + tags | On creation or significant update |
| byterover events | Event summary + timestamp + entities | On event recording |
| Feedback records | Feedback summary | On feedback recording |
| Research conclusions | Summarized findings | On promotion to long_term |

### What Does NOT Get Indexed in Qdrant
- Raw conversation transcripts (too noisy, use session search)
- Working memory (ephemeral)
- Full text of long documents (index summaries, point to full text)
- Skills (skills have their own keyword retrieval)

### Embedding Generation
1. Extract `content_summary` from the memory object
2. Prepend type and layer context: `"[{type}] [{layer}] {content_summary}"`
3. This gives the embedding more structural information for better retrieval

### Retrieval Pattern
```python
# Hybrid search: semantic + metadata filter
results = qdrant.search(
    collection_name="hermes_memories",
    query_vector=embedding,     # From user query
    query_filter={
        "must": [
            {"key": "layer", "match": {"any": ["core", "long_term"]}},
            {"key": "importance", "range": {"gte": 0.5}}
        ]
    },
    limit=10
)
```

## 5. Retrieval Order

Per the memory governance spec, Qdrant is the THIRD retrieval layer:

```
1. Core pointers (SOUL.md + memory.md)
   → Failed? Continue
2. Keyword/Tag search (fact_store + skills)
   → Failed? Continue
3. Semantic search (Qdrant — this layer)
   → Failed? Continue
4. Graph/Timeline search (Neo4j)
```

Qdrant should NOT be called if layers 1 or 2 already found sufficient results.

## 6. Re-ranking Strategy

After semantic retrieval:
1. Get top-20 by cosine similarity
2. Re-rank using:
   - Recency boost: newer → +10%
   - Importance boost: high importance → +20%
   - Layer priority: core > long_term > short_term
   - Tag overlap: matching tags → +15%
3. Return top-10 after re-ranking

## 7. Index Maintenance

- **Staleness check**: Re-embed memories when their content changes significantly
- **Cleanup**: Remove vectors for archived memories after 365 days
- **Deduplication**: Before inserting, search for cosine similarity > 0.95 and merge instead of duplicate
- **Batch updates**: Queue embedding generation; process in background, not during agent turns
