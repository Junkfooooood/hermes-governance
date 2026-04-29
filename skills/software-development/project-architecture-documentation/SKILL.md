---
name: project-architecture-documentation
description: "Create comprehensive Markdown architecture docs from an existing project's files, configs, docs, and code comments."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [architecture, documentation, codebase-analysis, handoff, systems-design, markdown]
    related_skills: [codebase-inspection, writing-plans, hermes-agent]
---

# Project Architecture Documentation

## When to Use

Use this skill when the user asks for a **systematic project architecture analysis or handoff document** based on an existing repository or runtime directory.

Trigger examples:

- "分析这个项目整体架构并输出 md 文件"
- "基于 README、配置、目录结构和代码注释生成架构文档"
- "写一份可用于后续开发/交接的架构说明"
- "不要简单罗列文件，要解释功能、逻辑链、模块关系、运行流程"
- "Document the architecture of this codebase/system from current files"

Do **not** use this for:

- Pure LOC/language statistics only — use `codebase-inspection`.
- Future implementation plans — use `writing-plans`.
- Hermes-specific setup/troubleshooting only — use `hermes-agent`, though this skill can combine with it for Hermes architecture docs.

## Core Principle

Architecture documentation should explain **function → logic chain → module relationships → runtime flow**, not just list files.

The final output should let a new developer answer:

1. What is this system for?
2. What are its major subsystems?
3. How does data/control flow through them?
4. Which files/components are the true entry points?
5. How do modules interact at runtime?
6. What are the operational risks and handoff priorities?

## Workflow

### 1. Clarify Scope by Default, Then Act

If the project root is obvious from the current working directory or user-provided path, proceed. Ask only if multiple roots would materially change the result.

Record:

- Project root(s)
- Expected output path
- Required sections or frameworks from the user
- Whether sensitive config may exist

### 2. Survey Existing Context and Skills

Before reading files, load relevant skills:

- This skill for architecture-doc workflow.
- `hermes-agent` if the target is Hermes Agent, `.hermes`, gateway, memory, tools, skills, or configuration.
- `codebase-inspection` if size/language breakdown is requested.
- `research-intelligence` only if external sources are required.

### 3. Discover the Project Shape

Use file search instead of shell `find/ls` where possible:

```python
search_files("*", target="files", path=project_root, limit=150)
search_files("README*", target="files", path=project_root, limit=50)
search_files("AGENTS.md|CLAUDE.md|SOUL.md|*.config.*|config.yaml|package.json|pyproject.toml", target="files", path=project_root, limit=100)
```

Look for:

- README / CONTRIBUTING / docs
- Configuration files
- Entrypoints / CLIs / servers / gateways
- Tool registries / plugin systems
- Runtime state directories
- Test directories
- Scripts and deployment files
- Project rules (AGENTS.md, CLAUDE.md, harness files)

### 4. Read High-Signal Files First

Prioritize files that explain structure and runtime behavior:

1. README / CONTRIBUTING / architecture docs
2. Main config files
3. Entrypoints (`main`, `cli`, `run`, gateway/server startup)
4. Registry/plugin/provider abstractions
5. Core loop / scheduler / dispatcher
6. Memory/state/session modules
7. Role/rules/protocol docs
8. Tests that encode invariants

Avoid dumping huge files into context; read slices around relevant sections.

### 5. Search for Runtime Concepts

Search for domain keywords named by the user and inferred from the project:

```python
search_files("agent|delegate|memory|gateway|scheduler|registry|provider|plugin|config", path=project_root, output_mode="content", context=1)
```

For multilingual/domain-specific concepts, search exact terms too, e.g. `三省`, `六部`, `governance`, `AMS`, `qdrant`, `neo4j`.

### 6. Build a Subsystem Map

For each subsystem, capture:

| Field | What to capture |
|---|---|
| Core positioning | Why it exists and what problem it solves |
| Entry points | Files/functions/commands where runtime begins |
| Inputs | User messages, config, files, events, API calls |
| Outputs | Responses, files, DB writes, tool results, logs |
| State | Where it persists data |
| Dependencies | Other modules/services/tools it calls |
| Failure modes | Known operational risks |

### 7. Write Function Logic Chains

For every major architecture, include a flow chain like:

```text
User/task input
→ runtime receives it
→ context/config is loaded
→ task is classified/planned
→ modules/tools/providers are invoked
→ state is updated
→ result is verified
→ output is returned
```

Do not stop at "module X handles Y". Explain how X participates in the runtime sequence.

### 8. Include Module Tables

For each architecture/subsystem, include a table:

```markdown
| 模块/文件/组件 | 作用 | 输入 | 输出 | 与其他模块的关系 |
|---|---|---|---|---|
```

Keep rows focused on high-signal modules. Do not list every file unless asked.

### 9. Handle Secrets and Sensitive Config Safely

When reading config:

- Never copy API keys, tokens, passwords, OAuth credentials, private URLs, or connection strings containing secrets.
- Replace with `[REDACTED]` if needed.
- Before finalizing, search the generated document for obvious secret patterns:

```python
search_files("sk-|api_key|token|password|secret", path=output_file, output_mode="content")
```

If matches are only safety guidance and no secrets, note that verification passed.

### 10. Recommended Document Structure

Use this structure unless the user requested another format:

```markdown
# [Project] Architecture Documentation

Generated: [date]
Scope: [paths]
Safety note: no secrets included

## 0. Executive overview
- System purpose
- Major subsystems
- End-to-end diagram/flow

# 1. [Architecture/Sub-system A]
## 1. Core positioning
## 2. Core functions
## 3. Internal modules
| Module | Role | Input | Output | Relationships |
## 4. Functional logic chain
## 5. Key mechanisms

# 2. [Architecture/Sub-system B]
...

# Cross-system runtime flows
# Development/handoff notes
# Risks and improvement opportunities
# Short conclusion
```

### 11. Save and Verify

Save to a stable docs path, e.g.:

```text
<project_root>/docs/<project>-architecture-YYYY-MM-DD.md
```

Then verify:

- File exists
- Byte size and line count
- First lines render correctly
- Secret scan passes
- The document addresses every required user section

Use a final response with the path and concise summary.

## Quality Checklist

Before returning:

- [ ] The doc is based on actual files/config/docs, not guessed architecture.
- [ ] Each requested architecture/subsystem has core positioning, functions, module table, logic chain, and mechanisms.
- [ ] Runtime flows explain control/data movement.
- [ ] It distinguishes implementation reality from inferred design intent.
- [ ] It omits secrets and credentials.
- [ ] It is saved as a Markdown file and verified.
- [ ] The final user response includes the absolute path.

## Common Pitfalls

1. **File listing instead of architecture** — convert file facts into runtime relationships.
2. **Reading too broadly** — prioritize high-signal docs/config/entrypoints and search targeted concepts.
3. **Leaking config secrets** — never quote credential-bearing lines; verify the generated doc.
4. **Ignoring user-specified frameworks** — if the user names layers/architectures, structure the document around them.
5. **No verification** — always confirm the output file exists and scan for sensitive patterns.
6. **Overfitting to one project** — save general workflow in the skill; put project-specific facts in memory only if durable.
