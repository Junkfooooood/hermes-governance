# Learning & Knowledge Store

## Purpose
Store structured learning notes, study materials, book/article summaries, and acquired knowledge. This domain tracks what you've learned and how you learned it.

## What Belongs Here
- Book and article summaries with key takeaways
- Course notes and study materials
- Research paper summaries
- Skill acquisition notes ("how I learned X")
- Mental models and frameworks from various disciplines
- Knowledge that crosses domain boundaries

## What Does NOT Belong Here
- Domain-specific professional knowledge (→ `fact_store/<domain>/`)
- Raw bookmarks/links without notes (→ session notes or discard)
- Methodology/how-to (→ `skills/`)
- Unverified claims (→ `memory/short_term/`)

## Entry Template

```markdown
---
id: learn_<YYYYMMDD>_<seq>
type: book_summary | article_note | course_note | mental_model | research_paper | skill_learning
layer: long_term (if validated) | short_term (if still processing)
importance: 0.0-1.0
stability: 0.0-1.0
confidence: 0.0-1.0
status: active
created: <ISO8601>
source: <book/article/course title, author, URL>
tags: [<domain tags>]
---

## <Title>

### Source
- Title:
- Author/Creator:
- URL/ISBN:
- Date accessed:

### Key Takeaways
1. <Takeaway 1>
2. <Takeaway 2>
3. <Takeaway 3>

### My Thoughts
<Personal reflection, critique, connection to existing knowledge>

### Actionable Insights
- [ ] <Thing to apply or test based on this learning>

### Related
- Prior knowledge: <links to related fact_store entries>
- Contradicts: <links to conflicting knowledge>
- Extends: <links to knowledge this builds upon>
```

## Examples

### Book Summary
```markdown
---
id: learn_20260428_001
type: book_summary
layer: long_term
importance: 0.75
stability: 0.70
confidence: 0.85
status: active
created: 2026-04-28T00:00:00Z
source: Example Book Title, Author Name
tags: [psychology, decision-making, cognitive-bias]
---

## Thinking, Fast and Slow — Daniel Kahneman

### Source
- Title: Thinking, Fast and Slow
- Author: Daniel Kahneman
- ISBN: 978-0374533557

### Key Takeaways
1. System 1 (fast, intuitive) and System 2 (slow, deliberate) thinking modes
2. Cognitive biases are systematic, not random — they can be predicted and mitigated
3. Loss aversion: losses hurt ~2x more than equivalent gains feel good
4. The planning fallacy: people systematically underestimate time/cost of future tasks
5. What You See Is All There Is (WYSIATI): we judge based on available information, ignoring missing information

### My Thoughts
The System 1/System 2 framework is useful for debugging my own decision-making. The planning fallacy directly applies to project estimation. Loss aversion explains many market behaviors.

### Actionable Insights
- [ ] When making important decisions, explicitly list what information is MISSING (counter WYSIATI)
- [ ] For project estimates, use reference class forecasting (look at similar past projects)
- [ ] Apply loss aversion awareness to investment decisions

### Related
- Prior knowledge: none yet
- Extends: decision-making framework
```

### Mental Model
```markdown
---
id: learn_20260428_002
type: mental_model
layer: long_term
importance: 0.80
stability: 0.85
confidence: 0.85
status: active
created: 2026-04-28T00:00:00Z
source: Various
tags: [mental-model, systems-thinking, problem-solving]
---

## Second-Order Thinking

### Source
- Various (Howard Marks, Charlie Munger, systems thinking literature)

### Key Takeaways
1. First-order thinking: "If I do X, Y will happen."
2. Second-order thinking: "If I do X, Y will happen, which will cause Z."
3. Most people stop at first-order. Competitive advantage comes from thinking one step further.
4. Ask: "And then what?" repeatedly to uncover hidden consequences.

### My Thoughts
This is the single most versatile mental model I've encountered. Applies to: investing (policy → market reaction → second-order effects), career decisions, product design, interpersonal dynamics.

### Actionable Insights
- [ ] Before any significant decision, write out: 1st order → 2nd order → 3rd order effects
- [ ] Review past decisions: which second-order effects did I miss?

### Related
- Extends: systems thinking, inversion, circle of competence
```
