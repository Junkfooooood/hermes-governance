---
name: research-intelligence
description: "High-quality external information collection, source triage, cross-verification, and synthesis."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, intelligence, source-quality, synthesis, evidence, external-information]
    related_skills: [arxiv, blogwatcher, llm-wiki, youtube-content, ocr-and-documents]
---

# Research Intelligence

Use this skill when the user asks for **high-quality external information gathering and synthesis**, not just a web search. It is for situations where correctness, source quality, triangulation, and concise conclusions matter.

## When to Use

Trigger this skill when the user asks to:

- Research a topic, company, product, technology, market, person, paper, or trend using external sources.
- Find the best/highest-quality information rather than many links.
- Compare claims across sources and summarize what is reliable.
- Produce an evidence-backed brief, landscape scan, due diligence memo, timeline, or trend analysis.
- Monitor or synthesize ongoing information from blogs/RSS, papers, GitHub repos, videos, docs, or news.
- Go beyond generic search results with filtering, credibility scoring, de-duplication, and synthesis.

Do **not** use for trivial lookups where one authoritative source answers the question directly.

## Core Principle

Separate the task into four layers:

1. **Question framing** — what decision or answer is needed?
2. **Source discovery** — gather candidates from multiple source classes.
3. **Source triage and verification** — score quality, remove duplicates, cross-check key claims.
4. **Synthesis** — produce conclusions with evidence, uncertainty, and open questions.

## Workflow

### 1. Frame the Research Question

Before gathering sources, identify:

- The exact question to answer.
- The decision/use case behind it.
- Time horizon: current snapshot, historical timeline, or forecast.
- Domain: academic, engineering, market, policy, investment, product, open-source, etc.
- Required output format: brief, table, timeline, comparison, recommendation, memo, or knowledge-base update.

If the user is ambiguous but the default is obvious, proceed and state the assumption.

### 2. Build a Source Plan

Use multiple source types where appropriate:

| Source type | Best for | Related skill/tool |
|---|---|---|
| Official docs/sites | Ground truth for products, APIs, policy, pricing | web extraction |
| Academic papers | Methods, evidence, prior work | `arxiv`, Semantic Scholar |
| GitHub/repos | Implementation reality, adoption, activity | GitHub/web; use Zread when repo understanding is needed |
| Blogs/RSS | Expert commentary, engineering details, updates | `blogwatcher` |
| Videos/transcripts | Talks, interviews, announcements | `youtube-content` |
| PDFs/reports | Whitepapers, filings, scanned docs | `ocr-and-documents` |
| Existing wiki/notes | Compounded prior knowledge | `llm-wiki`, `obsidian` |
| Social/community | Early signals, sentiment, issues | platform-specific tools, with low confidence unless corroborated |

### 3. Discover Candidates

Use targeted queries, not only broad search:

- Exact terms + synonyms.
- Official source query: `site:official-domain.com topic`.
- Critical query: `topic limitations`, `topic failure`, `topic benchmark`, `topic controversy`.
- Time query: include year/month for fast-moving domains.
- Entity query: founders/authors/orgs/repos/products.
- For papers: search arXiv/Semantic Scholar and inspect citations/references.
- For repos: inspect README, issues, commits, releases, contributors, stars/forks, package usage, and documentation.
- For GitHub repository intelligence, consider `zread.ai`, Zread MCP, or Zread CLI when available, especially for summarizing architecture, trends, or local projects.

### 4. Score Source Quality

Assign each important source a rough quality label:

- **A — Primary/authoritative:** official docs, source repo, paper, filing, standard, direct transcript.
- **B — Expert secondary:** reputable technical blogs, industry reports, cited analyses, maintainer commentary.
- **C — Useful but weak:** newsletters, summaries, media articles, community posts.
- **D — Low confidence:** unsourced claims, SEO spam, anonymous posts, copied content, unverifiable social chatter.

Prefer A/B sources for conclusions. Use C/D only as leads or sentiment signals.

Quality checks:

- Who authored it and what are their incentives?
- Is it primary or derivative?
- Is the date appropriate for the topic?
- Are claims backed by data, code, citations, or direct quotes?
- Is it corroborated by independent sources?
- Is there a conflict of interest or marketing angle?

### 5. De-duplicate and Cross-Verify

Before summarizing:

- Cluster duplicate articles and repeated claims.
- Keep the earliest/primary source when many posts cite the same origin.
- Cross-check central claims against at least two independent sources when possible.
- Explicitly mark claims as **confirmed**, **likely**, **contested**, or **unverified**.
- Preserve date/version information for fast-changing claims.

### 6. Synthesize

Default output structure:

```markdown
## Bottom line
[Direct answer in 3-6 bullets]

## Evidence table
| Claim | Confidence | Evidence | Notes |
|---|---:|---|---|

## Source quality
| Source | Type | Quality | Why it matters |
|---|---|---:|---|

## Timeline / landscape / comparison
[Use whichever format fits]

## Open questions
[What remains uncertain and how to resolve it]
```

For investment or strategic analysis, include:

- timeline of material events,
- actors/entities and relationships,
- leading indicators,
- risks/contradictions,
- what would change the conclusion.

### 7. Persist Valuable Work

If the research is likely to be reused:

- Use `llm-wiki` to ingest sources and update entity/concept/comparison/query pages.
- Use memory only for durable user preferences or stable environment facts, not research dumps.
- Save recurring collection procedures as skills rather than memory.

## Output Rules

- Cite or name sources for important claims.
- Distinguish facts from interpretation.
- Surface uncertainty rather than hiding it.
- Prefer a small set of high-quality sources over a long link dump.
- Do not over-trust search ranking.
- If source coverage is thin, say so and recommend the next retrieval step.

## Common Pitfalls

- Treating one blog summary as ground truth.
- Mixing old and new versions of a fast-moving project.
- Counting many copied articles as independent corroboration.
- Ignoring official docs or primary repos.
- Summarizing before filtering source quality.
- Forgetting to preserve provenance when adding findings to a wiki.
