# Semantic Index — Structure

## Purpose
The semantic index stores embedding-organized memory summaries for similarity-based retrieval. It works alongside Qdrant — the semantic_index directory contains the local index metadata and configuration; Qdrant stores the actual vectors.

## Directory Structure
```
semantic_index/
├── README.md                  # This file
├── index_config.yaml          # Index configuration
└── snapshots/                 # Periodic index snapshots
```

## What Gets Semantically Indexed
- Memory summaries from all layers (core, long_term, short_term)
- Fact summaries from fact_store
- Research conclusions
- Feedback summaries

## What Does NOT Get Semantically Indexed
- Raw full-text documents (use pointer retrieval)
- Session transcripts (use session search)
- Skills (use keyword/tag lookup)
- Working memory (discarded after session)

## Index Configuration

```yaml
# index_config.yaml
semantic_index:
  engine: qdrant
  embedding_model: text-embedding-3-small
  dimensions: 1536
  collections:
    - hermes_memories
    - hermes_facts
    - hermes_events
  re_ranking:
    enabled: true
    recency_weight: 0.10
    importance_weight: 0.20
    layer_priority_weight: 0.15
  deduplication:
    similarity_threshold: 0.95
    action: merge
  batch:
    max_batch_size: 100
    flush_interval_seconds: 300
  maintenance:
    reindex_on_schema_change: true
    stale_threshold_days: 365
```

## Retrieval Flow
1. User query → embed with same model
2. Search hermes_memories with layer + importance filter
3. If insufficient results, search hermes_facts
4. If still insufficient, search hermes_events
5. Re-rank combined results
6. Return top-10 with pointers to full content
