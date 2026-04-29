# Hermes Memory Harness v1

## 1. Purpose
This harness operationalizes the memory governance specification. The spec defines the rules; the harness enforces the workflow.

## 2. Responsibilities
The harness must:
- read the pointer layers first
- collect candidate memories from the appropriate store
- score and route new information
- write only summarized and standardized memory objects
- enforce lifecycle transitions
- archive or merge low-value items
- report context noise and retrieval pressure
- preserve the golden pointer-only layer

## 3. Execution pipeline
### Step 1: Load pointers
Read:
- `SOUL.md`
- `memory.md`

### Step 2: Determine task class
Classify the incoming work as one or more of:
- working context only
- short-term memory candidate
- long-term memory candidate
- core memory candidate
- skill candidate
- archive candidate
- graph candidate
- semantic candidate

### Step 3: Retrieve in order
Use retrieval order:
1. pointer layer
2. fact_store / skills
3. byterover / Qdrant
4. Neo4j

### Step 4: Score candidate items
Score each candidate on:
- importance
- stability
- reuse value
- time sensitivity
- confidence
- core relevance
- noise cost

### Step 5: Route the item
Route to one of:
- memory/working
- memory/short_term
- memory/long_term
- memory/core
- memory/archive
- fact_store
- skills
- byterover
- Neo4j

### Step 6: Apply lifecycle action
Possible actions:
- promote
- demote
- merge
- archive
- deprecate
- ignore

### Step 7: Summarize and commit
Before persistence, convert content into a pointer-first summary and record the storage target.

## 4. Harness rules
- Never expand golden files with narrative bodies.
- Never keep duplicate memory copies across layers without a canonical pointer.
- Never promote low-confidence items into core memory.
- Never let low-value recall dominate the working context.
- Always prefer summary plus pointer over raw text when persisting.

## 5. Noise-aware behavior
The harness should expose a simple diagnostic:
- current context noise ratio
- duplicate recall count
- candidate memory pressure
- suggested pruning actions

If noise is high, the harness should:
- compress context
- reduce recall breadth
- remove duplicate candidates
- defer nonessential recalls

## 6. Memory write policy
When writing memory:
- write full content only to the correct content layer
- write summary and pointer to the routing layer
- preserve the source and timestamp
- set a TTL for non-core items
- mark archive candidates explicitly

## 7. Skill lifecycle policy
Skills must be routed through the same harness.
- active -> low_frequency -> deprecated -> merged
- duplicate skills should be merged
- deprecated skills should stay recoverable
- canonical skills should keep forward pointers

## 8. Feedback loop policy
The harness must record real-world feedback when available.
A feedback entry should update the item state and weight.
It should also influence future routing decisions.

## 9. Minimal interface
The harness only needs three conceptual operations:
- `ingest(input)`
- `retrieve(query)`
- `govern(candidate)`

Each operation should return a pointer-first result set.
