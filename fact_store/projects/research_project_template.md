---
id: fact_20260428_prj_001
type: template
layer: long_term
importance: 0.70
stability: 0.70
confidence: 0.80
status: active
tags: [projects, research, template]
---

# Research Project Tracking Template

Use this template for tracking deep-dive research projects. A research project differs from a short-term hypothesis in scope and duration — it typically spans weeks to months and involves multiple data sources.

---

## Template

```markdown
---
id: project_<YYYYMMDD>_<seq>
type: research_project
status: planned | in_progress | completed | archived
topic: <Broad topic>
scope: <Specific scope boundaries>
started: <ISO8601>
target_completion: <ISO8601>
completed: <ISO8601> (if applicable)
tags: [<domain tags>]
---

## <Project Title>

### Research Question
<The specific question this research aims to answer>

### Scope Boundaries
- In scope: <what this covers>
- Out of scope: <what this explicitly does NOT cover>

### Hypothesis
<Initial thesis before deep research>

### Data Sources
| Source | Type | Status | Notes |
|--------|------|--------|-------|
| — | — | planned / collected / analyzed | — |

### Key Findings
| # | Finding | Confidence | Supporting Evidence |
|---|---------|-----------|---------------------|
| 1 | — | — | — |

### Conclusion
<Final thesis after research>

### Gap Analysis
Expected vs. actual finding:
- Expected: <what was hypothesized>
- Actual: <what was found>
- Gap: <why the difference>

### Related Memories
- Core thesis: `memory/core/<file>.md`
- Specific analysis notes: `memory/long_term/<file>.md`
- Graph node: `<neo4j_node_id>`

### Next Steps
- [ ] Action 1
- [ ] Action 2
```

---

## Active Projects

*No research projects active yet. Use the template above when initiating.*

---

## Completed Projects Index

| Project ID | Topic | Completed | Key Finding | Related |
|-----------|-------|-----------|-------------|---------|
| — | — | — | — | — |

---

## Cross-Reference
- Core investment principles: `memory/core/investment-principles.md`
- Research methodology: `memory/long_term/research-conclusions.md`
- Valuation frameworks: `fact_store/finance/valuation_principles.md`
- Graph tracking: `neo4j/schema.md`
