# AMS — Autonomous Memory Scoring & Routing Engine v1

## 1. Purpose

AMS is the decision brain of the Hermes memory system. It receives candidate memories (from mem0 extraction, conversation, task outputs, feedback) and decides:

- **Is this worth keeping?** → Score it
- **Where does it belong?** → Route to a layer
- **What should happen to it over time?** → Lifecycle actions

AMS does NOT store content. It makes decisions. Storage is handled by the respective layers.

## 2. Scoring Dimensions

Every candidate memory is scored on six dimensions, each 0.0–1.0:

| Dimension | What It Measures | High Score Example | Low Score Example |
|-----------|-----------------|--------------------|--------------------|
| **Importance** | How much does this matter to core objectives? | Investment thesis for primary portfolio position | Minor UI preference |
| **Stability** | How likely is this to remain true over time? | Proven valuation framework | Current market sentiment |
| **Reuse Value** | How often will this be needed in future? | DCF model template | One-time bug fix note |
| **Time Sensitivity** | How quickly does this decay? (inverted: 1.0 = timeless) | First principles of value investing | Today's stock price |
| **Confidence** | How certain are we this is correct? | Verified by 3+ independent sources | Speculative hypothesis |
| **Core Relevance** | How directly does this relate to user's primary goals? | Directly impacts investment decisions | Tangential curiosity |

### Scoring Guide

**Importance (0.0–1.0)**
- 0.9+: Directly impacts primary investment thesis or core agent behavior
- 0.7–0.9: Important to a major project or recurring workflow
- 0.4–0.7: Useful context, moderate impact
- 0.1–0.4: Nice to know, low impact
- 0.0–0.1: Trivia, noise

**Stability (0.0–1.0)**
- 0.9+: Mathematical truth, proven physical law, confirmed constitutional rule
- 0.7–0.9: Well-established framework, repeatedly validated methodology
- 0.4–0.7: Industry consensus, likely stable for months
- 0.1–0.4: Current trend, may shift
- 0.0–0.1: Breaking news, unverified rumor

**Reuse Value (0.0–1.0)**
- 0.9+: Used weekly or more; every similar task needs this
- 0.7–0.9: Used monthly; most related tasks reference this
- 0.4–0.7: Used quarterly; occasionally referenced
- 0.1–0.4: Used once or twice; situationally useful
- 0.0–0.1: Single-use; never needed again

**Time Sensitivity (0.0–1.0) (1.0 = timeless)**
- 0.9+: Permanent truth (laws of physics, mathematics)
- 0.7–0.9: Multi-year relevance (investment principles)
- 0.4–0.7: Months of relevance (quarterly patterns)
- 0.1–0.4: Days to weeks of relevance (current news cycle)
- 0.0–0.1: Hours of relevance (real-time price data)

**Confidence (0.0–1.0)**
- 0.9+: Verified by multiple independent sources + real-world feedback
- 0.7–0.9: Verified by one reliable source + logical consistency
- 0.4–0.7: Reasonable inference from known facts
- 0.1–0.4: Speculation based on pattern recognition
- 0.0–0.1: Pure guess, unverified claim

**Core Relevance (0.0–1.0)**
- 0.9+: Directly about user's primary investment thesis or core agent configuration
- 0.7–0.9: Related to active research project or recurring task
- 0.4–0.7: Adjacent domain, potentially useful
- 0.1–0.4: Interesting but not actionable
- 0.0–0.1: Completely unrelated to any known objective

## 3. Composite Score

```
composite = (
    importance      * 0.25 +
    stability       * 0.20 +
    reuse_value     * 0.15 +
    time_sensitivity * 0.10 +
    confidence      * 0.15 +
    core_relevance  * 0.15
)
```

### Weight Rationale
- **Importance** gets highest weight — valuable wrong information is more dangerous than trivial wrong information
- **Stability** is second — determines how long routing decisions remain valid
- **Confidence** and **Core Relevance** tie for third — uncertain or tangential information needs careful placement
- **Reuse Value** and **Time Sensitivity** are modifiers — they shift within-layer placement but rarely the layer itself

## 4. Routing Decision Matrix

| Composite Score | Stability | → Layer |
|-----------------|-----------|---------|
| ≥ 0.80 | ≥ 0.80 | **Core** — candidate for SOUL.md or memory.md pointer |
| ≥ 0.80 | < 0.80 | **Long-term** — stable enough for fact_store or skills |
| 0.50–0.79 | ≥ 0.60 | **Long-term** — valuable and reasonably stable |
| 0.50–0.79 | < 0.60 | **Short-term** — valuable but still evolving |
| 0.30–0.49 | any | **Short-term** — moderate value, set TTL |
| < 0.30 | any | **Discard** — not worth storing |

### Special Routing Rules

**Relationship-rich information** → Neo4j candidate
- If the memory connects 2+ entities, events, or theses, create a graph node
- Graph nodes can have lower composite scores if the relationship itself is valuable

**Semantically similar to existing memories** → Qdrant candidate
- If the memory is "like X but not exactly X," index for semantic retrieval
- Useful for pattern matching across domains

**Actionable methodology** → Skills candidate
- If the memory describes HOW to do something, not just WHAT is true
- Skills have their own lifecycle separate from fact memories

**Feedback/Outcome pair** → Feedback loop candidate
- If the memory contains a hypothesis + real-world outcome
- Always link to the original thesis via Neo4j

## 5. Lifecycle Trigger Conditions

### Promotion Triggers

**Short-term → Long-term**
ALL of:
- Composite score ≥ 0.60 on re-evaluation
- Stability ≥ 0.60 (confirmed by at least one real-world validation)
- At least 14 days since creation (survived initial decay period)
- Referenced or retrieved at least 2 times (proven utility)

**Long-term → Core**
ALL of:
- Composite score ≥ 0.80 on re-evaluation
- Stability ≥ 0.85 (confirmed by 3+ independent validations)
- At least 90 days at long-term level
- Referenced in 5+ distinct sessions
- Human confirmation (core memory changes require high confidence — Law 3 of memory governance)

### Demotion Triggers

**Long-term → Short-term**
ANY of:
- Composite score drops below 0.50 on re-evaluation
- Stability drops below 0.40 (new information contradictory)
- Not referenced in 90 days
- Superseded by a newer, higher-scored memory on same topic

**Short-term → Archive**
ANY of:
- TTL expired (default: 30 days for short-term)
- Task completed and no follow-up flagged
- Composite score drops below 0.30
- Superseded or merged into another memory

### Archive Triggers

**Any layer → Archive**
- Explicitly deprecated (outdated, wrong, superseded)
- Merged into a canonical memory (merged copy archived)
- TTL expired with no renewal
- Explicitly marked for archival by AMS review

### Skills Demotion/Deprecation

**Active → Low Frequency**
- Not invoked in 30 days
- Success rate < 50% on last 3 invocations
- Overlaps significantly (>70%) with another active skill

**Low Frequency → Deprecated**
- Not invoked in 90 days
- Superseded by a new skill
- Domain no longer relevant to active objectives

## 6. AMS Self-Assessment Prompt

Agents can run this to evaluate a candidate memory:

```
## AMS Evaluation — Candidate Memory

### The Information
[Paste the candidate memory content here]

### Scoring
Rate each dimension 0.0–1.0:

1. Importance: ___ (How much does this matter?)
   Why: ___

2. Stability: ___ (How likely to remain true?)
   Why: ___

3. Reuse Value: ___ (How often needed in future?)
   Why: ___

4. Time Sensitivity: ___ (1.0 = timeless, 0.0 = hours)
   Why: ___

5. Confidence: ___ (How certain are we?)
   Why: ___

6. Core Relevance: ___ (How directly related to primary goals?)
   Why: ___

### Composite
Score: ___ (use formula in ams-engine.md §3)

### Routing Decision
Layer: ___ (use matrix in ams-engine.md §4)
Special routing: Neo4j? Qdrant? Skills? Feedback? ___

### Lifecycle
Initial TTL: ___ (days)
Review schedule: ___ (next evaluation date)
Promotion conditions: ___
```

## 7. Periodic Review Schedule

AMS should review memories on a schedule:

| Layer | Review Interval | Action |
|-------|----------------|--------|
| **Core** | 180 days | Re-validate stability; confirm still core-worthy |
| **Long-term** | 90 days | Re-score; check for staleness or promotion eligibility |
| **Short-term** | 30 days or TTL | Decide: promote, keep, or archive |
| **Working** | End of session | Discard (default) or summarize → short-term |
| **Archive** | 365 days | Purge truly obsolete items; keep audit trail |

## 8. AMS Integration Points

```
Conversation/Task Output
        │
        ▼
    mem0 Extraction ─── extracts candidate memories
        │
        ▼
    AMS Scoring ─── scores + routes each candidate
        │
        ├──→ memory/core/       (composite ≥ 0.80 + stable)
        ├──→ memory/long_term/  (composite 0.50–0.79 + stable)
        ├──→ memory/short_term/ (composite 0.30–0.49 or valuable but unstable)
        ├──→ fact_store/        (structured, keyword-friendly)
        ├──→ skills/active/     (actionable methodology)
        ├──→ Neo4j              (relationship-rich)
        ├──→ Qdrant             (semantically indexable)
        └──→ Discard            (below threshold)
```

AMS is called:
1. **On session end** — evaluate all candidate memories from the session
2. **On periodic review** — re-evaluate existing memories against lifecycle triggers
3. **On explicit request** — agent or user asks AMS to evaluate a specific memory
