# Hermes Memory Governance Specification v1

## 1. Purpose
Hermes uses a layered memory system to reduce noise, preserve attention, and support investment analysis workflows that depend on time, causality, and durable reasoning.

## 2. Core design rule
The golden space of the agent must remain pointer-only.
- `SOUL.md` stores identity, principles, and routing rules.
- `memory.md` stores the compact memory map.
- Neither file should contain large narrative memory bodies.
- The actual knowledge must live in the layered stores below.

## 3. Memory layers
### 3.1 Working memory
- Scope: current turn, current tool state, current reasoning state.
- Persistence: none unless summarized.
- Rule: do not write raw working memory to durable storage.

### 3.2 Short-term memory
- Scope: recent tasks, temporary hypotheses, active session context.
- Persistence: limited TTL.
- Rule: may be promoted, summarized, or archived after task completion.

### 3.3 Long-term memory
- Scope: validated reusable knowledge, stable research conclusions, recurring methods.
- Persistence: durable.
- Rule: must be deduplicated and periodically reviewed.

### 3.4 Core memory
- Scope: long-lived goals, stable preferences, decision principles, protected anchors.
- Persistence: highest.
- Rule: changes require high confidence or explicit user confirmation.

### 3.5 Archived memory
- Scope: expired, deprecated, superseded, or merged content.
- Persistence: retained for audit and recovery.
- Rule: excluded from default recall.

## 4. Storage responsibilities
### 4.1 Local filesystem
- Carries full text notes, research reports, and durable artifacts.
- Acts as the正文 layer.
- No semantic or graph reasoning is assumed here.

### 4.2 fact_store
- Carries keyword/tag-retrievable structured facts.
- Best for stable rules, frameworks, templates, and finance notes.

### 4.3 skills
- Carries reusable procedures, workflows, decision templates, and operational rules.
- Must support merge and deprecation lifecycle.

### 4.4 byterover
- Carries semantic recall and timeline recall.
- Primary use: similar-case retrieval, research history, and time-ordered analysis.

### 4.5 Qdrant
- Provides vector similarity retrieval.
- Used for semantic recall when keywords are insufficient.

### 4.6 Neo4j
- Provides relationship, causality, and timeline retrieval.
- Required for investment analysis workflows that depend on event ordering and causal chains.

### 4.7 AMS
- Memory governance center.
- Decides where memory belongs, whether it should be promoted, demoted, archived, merged, or ignored.
- Must not be the sole storage for long-form content.

### 4.8 mem0
- Memory extraction and normalization layer.
- Converts raw conversation and task outputs into standardized memory objects.

## 5. Memory object schema
Every persisted memory item should conform to a standard schema.

Required fields:
- `id`
- `type`
- `layer`
- `importance`
- `stability`
- `tags`
- `source`
- `timestamp`
- `ttl`
- `status`
- `pointer`
- `content_summary`

Example:

```yaml
id: mem_20260428_001
type: investment_thesis
layer: long_term
importance: 0.87
stability: 0.76
tags:
  - finance
  - valuation
source: conversation
timestamp: 2026-04-28T10:00:00Z
ttl: P90D
status: active
pointer: fact_store/finance/valuation_principles.md
content_summary: 关于某标的估值假设与风险点的摘要
```

## 6. Lifecycle policy
### 6.1 States
- working
- short_term
- long_term
- core
- archived
- deprecated

### 6.2 Promotion rules
- Working -> short_term when the current task still needs continuity.
- Short_term -> long_term when validated and reusable.
- Long_term -> core when highly stable and core to behavior.

### 6.3 Demotion rules
- Long_term -> short_term when value decays or becomes contextual.
- Short_term -> archived when task completes or TTL expires.
- Non-core items must eventually be eligible for archive.

### 6.4 Merge rules
- Duplicate or overlapping memories should be merged rather than duplicated.
- The canonical memory keeps the primary pointer.
- Merged memories move to archive or merged history.

### 6.5 Deprecation rules
- Outdated skills, repeated facts, and low-use items should be deprecated.
- Deprecated items stay recoverable but are excluded from default recall.

## 7. Retrieval policy
Retrieval order is strictly layered:
1. Core pointers in `SOUL.md` and `memory.md`
2. Keyword/tag lookup in `fact_store/` and `skills/`
3. Semantic recall in `byterover/` and Qdrant
4. Relationship/timeline recall in Neo4j

Rules:
- Start with the smallest useful context.
- Expand only if the earlier layer is insufficient.
- Deduplicate and rank results before returning them to the agent.

## 8. Noise control policy
The agent must actively minimize context noise.

Required behaviors:
- Estimate how much of current context is redundant or low value.
- Prefer pointers over full text.
- Summarize repeated material.
- Down-rank low-value or duplicated recall.
- Avoid flooding the working context with full history.

Suggested operational question:
- "What is the current context noise ratio?"

## 9. Skills governance
Skills are governed by the same lifecycle discipline as memory.

Rules:
- Active skills may be merged when they overlap.
- Low-frequency skills should be demoted if rarely used.
- Deprecated skills remain archived but should not appear in default recall.
- Merged skills must point to a canonical replacement.

## 10. Feedback loop
Hermes should learn from reality, not just from conversation.

Feedback loop:
1. Form hypothesis
2. Take action
3. Observe real-world feedback
4. Compare expected vs actual result
5. Update memory weights or status
6. Promote, demote, merge, or archive as needed

A feedback record should include:
- related memory id
- hypothesis
- action
- feedback
- result
- next action

## 11. AMS decision rubric
AMS should score candidate memory items using:
- importance
- stability
- reuse value
- time sensitivity
- confidence
- relation to core objectives

Typical outcomes:
- high importance + high stability -> core or long-term
- high importance + low stability -> short-term until validated
- low importance + reusable -> fact_store or skills
- low importance + duplicate -> archive or merge
- relationship-rich -> Neo4j
- semantically similar but keyword-unclear -> Qdrant

## 12. Implementation priority
1. Keep golden files pointer-only.
2. Make lifecycle management explicit.
3. Normalize memory objects.
4. Wire retrieval layers in the correct order.
5. Add noise awareness and real-world feedback loops.
6. Continuously merge, archive, and prune.
