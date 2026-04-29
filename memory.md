# Hermes memory map

## Core layer
- `SOUL.md` — core identity, principles, and routing rules
- `memory.md` — compact pointer map
- `memory/memory-governance-spec.md` — governance specification
- `memory/harness.md` — enforcement and operational harness
- `memory/core/` — stable anchors only

## Memory lifecycle layers
- `memory/working/` — ephemeral task state
- `memory/short_term/` — recent context and temporary hypotheses
- `memory/long_term/` — validated reusable knowledge and schemas
- `memory/archive/` — expired, deprecated, or superseded memory

## Retrieval layers
- `fact_store/` — keyword/tag friendly facts
- `skills/` — reusable procedures and playbooks
- `byterover/` — semantic index, timeline index, and events
- `neo4j/` — relationships, causality, and time-ordered facts
- `qdrant` — vector recall service

## Governance layers
- `harness/` — universal agent rules, roles, and collaboration protocols
- `ams-api` — memory governance and orchestration
- `mem0` — extraction, normalization, and write orchestration

## Retrieval order
1. Core pointers
2. Keyword/tag facts and skills
3. Semantic recall
4. Graph / timeline recall

## Operating rule
- Keep this file short.
- Store pointers, not正文.
- Prefer promotion, demotion, and archiving over unbounded growth.
