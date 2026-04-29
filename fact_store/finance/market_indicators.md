---
id: fact_20260428_fin_002
type: reference
layer: long_term
importance: 0.80
stability: 0.75
confidence: 0.80
status: active
tags: [finance, indicators, macro, market]
---

# Market Indicators Reference

## 1. Macro Indicators

### GDP & Growth
| Indicator | What It Signals | Frequency | Lead/Lag |
|-----------|----------------|-----------|----------|
| Real GDP Growth | Overall economic health | Quarterly | Lagging |
| GDP Nowcasts (Fed Atlanta GDPNow) | Real-time GDP estimate | Continuous | Coincident |
| PMI (Manufacturing & Services) | Business activity expansion/contraction | Monthly | Leading |

### Labor Market
| Indicator | What It Signals | Frequency | Lead/Lag |
|-----------|----------------|-----------|----------|
| Nonfarm Payrolls | Job creation pace | Monthly | Coincident |
| Initial Jobless Claims | Layoff velocity | Weekly | Leading |
| JOLTS Job Openings | Labor demand strength | Monthly | Leading |
| Wage Growth (AHE) | Inflation pressure from labor | Monthly | Leading |

### Inflation
| Indicator | What It Signals | Frequency | Lead/Lag |
|-----------|----------------|-----------|----------|
| CPI (Headline & Core) | Consumer price changes | Monthly | Lagging |
| PCE (Fed preferred) | Broader consumer inflation | Monthly | Lagging |
| PPI | Pipeline price pressure | Monthly | Leading |
| 5y5y Inflation Swap | Market-implied long-term inflation | Daily | Leading |
| TIPS Breakevens | Bond market inflation expectations | Daily | Coincident |

### Monetary Policy
| Indicator | What It Signals | Frequency | Lead/Lag |
|-----------|----------------|-----------|----------|
| Fed Funds Rate | Policy stance | Per meeting | Coincident |
| Dot Plot (SEP) | FOMC members' rate projections | Quarterly | Leading |
| Fed Funds Futures | Market-implied rate path | Daily | Leading |
| Fed Balance Sheet | Quantitative tightening/easing | Weekly | Coincident |
| Financial Conditions Index | Holistic financial tightness | Daily/Weekly | Coincident |

---

## 2. Market Indicators

### Valuation
| Indicator | What It Signals | Normal Range | Extreme Signals |
|-----------|----------------|-------------|-----------------|
| S&P 500 P/E (TTM) | Current market valuation | 15-20x | <12x: oversold; >25x: overbought |
| S&P 500 P/E (Forward) | Earnings-expected valuation | 14-19x | Compare to TTM for earnings direction |
| Shiller CAPE | Cyclically-adjusted valuation | 15-25x | >30x: caution (historical) |
| Equity Risk Premium | Stocks vs. bonds attractiveness | 3-5% | <2%: stocks expensive vs bonds |
| Buffett Indicator | Market cap / GDP | 80-120% | >150%: significantly overvalued |

### Sentiment & Breadth
| Indicator | What It Signals | Signal |
|-----------|----------------|--------|
| VIX (Fear Index) | Implied volatility, market fear | <15: complacency; >30: panic |
| Put/Call Ratio | Options market sentiment | >1.0: bearish extreme; <0.6: bullish extreme |
| Advance/Decline Line | Market breadth | Divergence from index = weakening |
| AAII Sentiment Survey | Retail investor sentiment | Extreme readings are contrarian signals |
| % Stocks Above 200-day MA | Technical health of market | <30%: oversold; >80%: overbought |

### Credit Markets
| Indicator | What It Signals | Signal |
|-----------|----------------|--------|
| High Yield Spread | Risk appetite in credit | Widening = risk-off; tightening = risk-on |
| Investment Grade Spread | Corporate credit health | Similar interpretation |
| TED Spread | Interbank lending stress | >1%: credit stress (rare post-2008) |
| 2y/10y Yield Curve | Recession probability | Inversion = recession signal (12-18 month lead) |
| 3m/10y Yield Curve | Fed policy stance | Inversion = policy too tight |

---

## 3. Sector-Specific Indicators

### Technology / Semiconductor
| Indicator | What It Signals | Source |
|-----------|----------------|--------|
| SEMI Book-to-Bill | Equipment demand | SEMI |
| DRAM/NAND spot prices | Memory cycle position | DRAMeXchange, TrendForce |
| Global semiconductor revenue | Industry cycle | SIA, WSTS |
| Cloud CapEx (AWS/GCP/Azure) | Data center demand | Company earnings |
| TSMC monthly revenue | Leading edge demand proxy | TSMC |

### Real Estate
| Indicator | What It Signals | Source |
|-----------|----------------|--------|
| Case-Shiller Home Price Index | Housing price trends | S&P |
| Housing Starts / Building Permits | Supply pipeline | Census Bureau |
| 30-Year Fixed Mortgage Rate | Affordability driver | Freddie Mac |
| Existing Home Sales | Market activity level | NAR |

---

## 4. Indicator Interpretation Rules

1. **Never trade a single indicator.** Look for confirming signals across macro, market, and sector levels.
2. **Know the lead/lag.** Using a lagging indicator for timing will always be late.
3. **Extremes matter more than middles.** Most indicators are noisy in normal ranges. The signal is at extremes.
4. **Context matters.** Low P/E in a recession is different from low P/E in a boom — don't treat them the same.
5. **The trend matters more than the level.** A rising PMI at 48 is more bullish than a falling PMI at 55.

---

## Cross-Reference
- Valuation frameworks: `fact_store/finance/valuation_principles.md`
- Investment patterns: `fact_store/patterns/investment_patterns.md`
- Graph schema (for causal chains): `neo4j/schema.md`
