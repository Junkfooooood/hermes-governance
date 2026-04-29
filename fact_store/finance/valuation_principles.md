---
id: fact_20260428_fin_001
type: framework
layer: long_term
importance: 0.85
stability: 0.85
confidence: 0.85
status: active
tags: [finance, valuation, framework, dcf, comparable, ddm]
---

# Valuation Principles

## 1. Discounted Cash Flow (DCF)

### Core Formula
```
Enterprise Value = Σ (FCF_t / (1 + WACC)^t) + Terminal Value / (1 + WACC)^n
```

### Key Inputs
| Input | Source | Stability |
|-------|--------|-----------|
| Free Cash Flow projection | Company financials + industry growth rates | Low — varies by assumption |
| WACC | Risk-free rate + equity risk premium + beta + cost of debt | Medium — changes with macro |
| Terminal growth rate | Long-term GDP growth + industry adjustment | High — typically 2-3% |
| Projection period | Industry cycle length | Medium — 5-10 years standard |

### When DCF Works Best
- Stable, mature companies with predictable cash flows
- Companies with a clear competitive moat
- Industries with long visibility (utilities, infrastructure)

### When DCF Fails
- Early-stage companies with no/negative cash flow
- Highly cyclical industries at peak/trough
- Companies undergoing major transformation
- When small changes in terminal growth rate swing valuation by >30%

### Common Pitfalls
1. **Garbage in, garbage out**: Overly precise revenue projections 5+ years out
2. **Terminal value dominance**: When TV > 80% of total value, the model is mostly terminal assumption
3. **WACC manipulation**: Tweaking WACC to get the "right" answer
4. **Ignoring dilution**: For companies with heavy stock-based compensation

---

## 2. Comparable Company Analysis (Comps)

### Selecting Comparables
- Same industry (GICS sub-industry level)
- Similar business model (asset-light vs. asset-heavy)
- Similar growth stage (high growth vs. mature)
- Similar geographic exposure
- Similar market cap (within 0.5x–2x range)

### Standard Multiples
| Multiple | Best For | Pitfall |
|----------|----------|---------|
| EV/EBITDA | Capital-intensive industries | Ignores CapEx intensity differences |
| P/E | Mature, profitable companies | Distorted by one-time items, capital structure |
| P/B | Financials, asset-heavy | Misleading for asset-light/IP-heavy companies |
| EV/Sales | Growth companies without profit | Ignores margin differences |
| P/FCF | Quality check | Volatile quarter-to-quarter |

### Interpretation Rules
- Never use a single multiple in isolation
- Always understand WHY a company trades at a premium/discount
- Historical multiple range gives context for "cheap" vs. "expensive"
- Adjust for differences in growth, margins, and ROIC

---

## 3. Dividend Discount Model (DDM)

### Best For
- Mature financial institutions
- Utilities with regulated returns
- Companies with explicit dividend policies

### Limitations
- Not applicable to companies that don't pay dividends
- Assumes dividend policy reflects true earnings power
- Misses value from buybacks

---

## 4. Scenario Analysis Framework

For high-uncertainty situations, use scenario analysis instead of point estimates:

```
Expected Value = Σ (Scenario_Value_i × Probability_i)
```

### Scenario Construction
1. **Base case** (50-60% probability): Most likely outcome
2. **Bull case** (20-25%): Upside scenario with specific triggers
3. **Bear case** (20-25%): Downside scenario with specific triggers

### Anti-Patterns
- False precision: 3+ decimal places on probabilities that are guesses
- Anchoring: Base case drifts toward recent stock price
- Asymmetric scenarios: Only modeling upside or only modeling downside

---

## 5. Moat Assessment Framework

### Five Sources of Moat (Morningstar framework)
1. **Switching costs**: How painful is it for customers to leave?
2. **Intangible assets**: Brands, patents, regulatory licenses
3. **Cost advantage**: Structural lower cost that competitors can't replicate
4. **Network effects**: Each additional user increases value for all users
5. **Efficient scale**: Market sized for one or few profitable players

### Moat Strength Indicators
- ROIC > WACC sustained over 10+ years
- Stable or growing market share
- Pricing power (can raise prices without losing volume)
- Industry-leading margins

### Moat Erosion Signals
- ROIC trending toward WACC
- Market share declining
- Customer complaints about price increases
- New entrants succeeding despite incumbent advantages

---

## Cross-Reference
- Core principles: `memory/core/investment-principles.md`
- Research methodology: `memory/long_term/research-conclusions.md`
- Market indicators: `fact_store/finance/market_indicators.md`
- Graph schema: `neo4j/schema.md`
