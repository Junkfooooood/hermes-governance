---
id: ltm_20260428_001
type: methodology
domain: finance
layer: long_term
importance: 0.85
stability: 0.80
confidence: 0.85
status: active
created: 2026-04-28T00:00:00Z
last_reviewed: 2026-04-28T00:00:00Z
review_due: 2026-07-27T00:00:00Z
tags: [investment, methodology, research]
---

> **Domain: Finance** — This is a domain-specific long-term memory. See [`learned-knowledge.md`](learned-knowledge.md) for a domain-agnostic example.


## Research Methodology — Time-Series Validated Analysis

### Summary
The user's preferred research methodology combines fundamental analysis with rigorous time-series validation. Every thesis must be tracked through time with explicit checkpoint markers. The methodology emphasizes causal chain reconstruction over correlation-based analysis. Neo4j serves as the primary timeline reconstruction tool.

### Evidence Chain
- Source 1: User workflow definition — 2026-04-28, confidence: 0.90
- Validation: Consistent with documented memory system design principles

### Method Steps
1. Form thesis with explicit expected outcomes and timeline
2. Record thesis in Neo4j as a Thesis node linked to relevant Entity nodes
3. Define checkpoint intervals (when to re-evaluate)
4. At each checkpoint, record real-world data vs. expected
5. Update thesis confidence based on gap analysis
6. If thesis invalidated, trace causal chain to find where the model broke
7. Archive invalidated thesis with invalidation reason

### Related Memories
- Core: `memory/core/investment-principles.md`
- Valuation: `fact_store/finance/valuation_principles.md`
- Feedback loop: `memory/feedback-loop-investment.md`
- Timeline tracking: `neo4j/schema.md`
