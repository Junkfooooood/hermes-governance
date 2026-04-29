---
id: fact_20260428_ppl_001
type: template
layer: long_term
importance: 0.70
stability: 0.65
confidence: 0.75
status: active
tags: [people, analyst, template]
---

# Analyst / Investor Tracking Template

Use this template to track perspectives from specific analysts, fund managers, or thought leaders whose views inform investment decisions.

---

## Template

```markdown
---
id: people_<YYYYMMDD>_<seq>
type: analyst_tracker
name: <Full Name>
affiliation: <Firm / Independent>
specialization: <Sector / Strategy / Macro>
status: active_tracking | archived
since: <ISO8601 — when tracking started>
---

## <Name> — <Affiliation>

### Thesis Summary
<Their overarching investment philosophy or current macro view, 2-3 sentences>

### Track Record
| Date | Call/Prediction | Outcome | Accuracy |
|------|----------------|---------|----------|
| — | — | — | — |

### Current Positions / Views
| Topic | View | Conviction (1-10) | Last Updated |
|-------|------|--------------------|--------------|
| — | — | — | — |

### Contrarian Indicators
<When this person is extremely bullish: what does that mean? Extremely bearish?>

### Biases / Blind Spots
<Known cognitive or analytical biases>

### Sources
- Primary: <where they publish, blog, podcast, Twitter>
- Secondary: <who covers/interviews them>
```

---

## Active Tracked Analysts

*No analysts tracked yet. Use the template above when adding.*

---

## Cross-Reference
- Investment thesis tracking: `memory/short_term/active-hypotheses.md`
- Graph schema (Person nodes): `neo4j/schema.md`
- Feedback loop (track analyst accuracy): `memory/feedback-loop-investment.md`
