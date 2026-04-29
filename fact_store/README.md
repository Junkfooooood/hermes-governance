# Fact Store — Multi-Domain Knowledge Base

Keyword/tag-friendly structured facts live here. This layer is optimized for stable, retrievable knowledge — facts, frameworks, templates, and patterns.

## Domains

| Domain | Directory | Purpose |
|--------|-----------|---------|
| **Daily** | [`daily/`](daily/) | Daily observations, personal notes, life events, general knowledge |
| **Learning** | [`learning/`](learning/) | Books, articles, courses, mental models, skill acquisition |
| **Finance** | [`finance/`](finance/) | Valuation frameworks, market indicators, investment patterns |
| **People** | [`people/`](people/) | Tracking perspectives, relationships, social context |
| **Projects** | [`projects/`](projects/) | Research project tracking, milestones, findings |

## Adding a New Domain

1. Create a subdirectory: `fact_store/<domain>/`
2. Add a `README.md` explaining the domain's scope and entry templates
3. Tag entries with the domain tag for cross-domain search
4. Register the domain in this file's domain table

## Retrieval

Fact store is the second retrieval layer (after core pointers):
```
1. Core pointers (SOUL.md + memory.md)
2. Keyword/tag search in fact_store/ ← THIS LAYER
3. Semantic search (Qdrant)
4. Graph/timeline (Neo4j)
```

All entries use frontmatter tags for keyword retrieval. No semantic or graph reasoning is assumed at this layer.
