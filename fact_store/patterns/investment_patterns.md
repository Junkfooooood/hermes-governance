---
id: fact_20260428_pat_001
type: pattern
layer: long_term
importance: 0.75
stability: 0.70
confidence: 0.70
status: active
tags: [investment, patterns, cycles, behavioral]
---

# Investment Patterns

## 1. Market Cycles

### Sector Rotation Model
The classic sector rotation through economic cycles:

```
EARLY CYCLE (Recovery)
  Leading: Financials, Consumer Discretionary, Technology
  Lagging: Utilities, Consumer Staples

MID CYCLE (Expansion)
  Leading: Technology, Industrials, Energy
  Lagging: Consumer Staples, Utilities

LATE CYCLE (Peak)
  Leading: Energy, Materials, Healthcare
  Lagging: Consumer Discretionary, Technology

RECESSION
  Leading: Utilities, Consumer Staples, Healthcare
  Lagging: Financials, Industrials, Real Estate
```

### Pattern Validity Notes
- Sector rotation is a tendency, not a rule
- Central bank intervention has distorted traditional cycle patterns
- Technology has become less cyclical in recent decades (structural shift)
- Use as a framework for hypothesis generation, not mechanical allocation

### Bear Market Typology
| Type | Cause | Typical Duration | Recovery Pattern |
|------|-------|-----------------|------------------|
| Cyclical | Economic recession | 6-18 months | V-shaped if policy responds |
| Structural | Valuation bubble + systemic risk | 18-36 months | U-shaped or L-shaped |
| Event-driven | External shock (war, pandemic) | 1-6 months | V-shaped if shock is transient |

---

## 2. Behavioral Patterns

### Common Cognitive Biases in Investing

| Bias | Manifestation | Mitigation |
|------|--------------|------------|
| **Confirmation Bias** | Seeking information that confirms existing thesis | Explicitly list evidence AGAINST your thesis |
| **Recency Bias** | Overweighting recent events | Look at 10+ year charts |
| **Anchoring** | Fixating on purchase price or recent high | Re-evaluate: "Would I buy today at this price?" |
| **Loss Aversion** | Holding losers too long, selling winners too early | Pre-commit to sell rules before entering |
| **Narrative Fallacy** | Creating coherent stories from random events | Track predictions vs. outcomes quantitatively |
| **Overconfidence** | Overestimating precision of forecasts | Always use ranges, not point estimates |

### Market Sentiment Cycle

```
Optimism → Excitement → Thrill → Euphoria (TOP)
                                         │
                                         ▼
                                     Anxiety
                                         │
                                         ▼
                                     Denial
                                         │
                                         ▼
                                      Fear
                                         │
                                         ▼
                                   Capitulation (BOTTOM)
                                         │
                                         ▼
                                    Despondency
                                         │
                                         ▼
    (BOTTOM) Depression ←─── Panic ←───┘
         │
         ▼
       Hope
         │
         ▼
      Relief
         │
         ▼
     Optimism (cycle repeats)
```

---

## 3. Reversal Patterns

### Indicators of Mean Reversion Opportunity

- **Valuation**: Sector P/E at 10-year low while earnings are stable
- **Sentiment**: Universal bearishness (magazine covers, analyst downgrades)
- **Positioning**: Institutional ownership at multi-year lows
- **Catalyst**: Upcoming event that could change narrative

### Momentum Continuation Patterns

- **Earnings revisions**: Positive earnings revision trend (not just one quarter)
- **Price trend**: Above 50-day and 200-day moving averages
- **Volume**: Increasing volume confirming price direction
- **Leadership**: Sector leading market in relative strength

---

## 4. Event-Driven Patterns

### Earnings Surprise Chain
```
Earnings Beat → Guidance Raise → Analyst Upgrades → Multiple Expansion
                                                         │
                                                         ▼
                                              Continued Outperformance
                                              
Earnings Miss → Guidance Cut → Analyst Downgrades → Multiple Compression
                                                         │
                                                         ▼
                                              Further Underperformance
```
Pattern: The first revision is rarely the last — estimate revision trends persist.

### Fed Policy Cycle Impact
```
Hiking Cycle Begins → P/E Compression (especially growth/high-multiple)
  │
  ▼
Hiking Cycle Peaks → Market bottoms BEFORE the last hike (6-9 month lead)
  │
  ▼
Cutting Cycle Begins → Initial sell-off (recession fear) → Recovery
```
Pattern: Markets lead Fed policy by 6-9 months.

---

## 5. Pattern Usage Guidelines

1. **Patterns are probabilistic, not deterministic.** A pattern says "this happens 60-70% of the time," not "this will happen."
2. **Every cycle is different.** The sector rotation of 2008 looked different from 2020. Understand the unique drivers.
3. **Patterns fail when everyone sees them.** If a pattern becomes too widely recognized, the market front-runs it.
4. **Combine patterns with fundamentals.** A technical pattern with no fundamental catalyst is noise.
5. **Record pattern outcomes.** Every pattern-based prediction should go to the feedback loop.

---

## Cross-Reference
- Market indicators (check against patterns): `fact_store/finance/market_indicators.md`
- Feedback loop (record pattern predictions): `memory/feedback-loop-investment.md`
- Graph schema (pattern instances as Neo4j nodes): `neo4j/schema.md`
