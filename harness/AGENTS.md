# Hermes Harness — Agent Entry Point

Every agent in the Hermes ecosystem must read this file first. It is the map — not the manual. Detailed rules live in the referenced documents. Load them on demand, not all at once.

---

## Quick Nav

| What you need | Where to find it |
|---|---|
| Immutable laws (ALL agents must obey) | [`constitution.md`](constitution.md) |
| Your role definition | [`roles/`](roles/) — pick one |
| How to collaborate with other agents | [`rules/collaboration.md`](rules/collaboration.md) |
| How to delegate tasks | [`rules/delegation.md`](rules/delegation.md) |
| How to communicate with other agents | [`rules/communication.md`](rules/communication.md) |
| What you can and cannot do | [`rules/safety.md`](rules/safety.md) |
| Quality standards for your output | [`rules/quality.md`](rules/quality.md) |
| Your lifecycle (spawn → retire) | [`rules/lifecycle.md`](rules/lifecycle.md) |
| How to handshake with other agents | [`protocols/handshake.md`](protocols/handshake.md) |
| Standard message format | [`protocols/message-spec.md`](protocols/message-spec.md) |
| Delegation contract format | [`protocols/delegation-spec.md`](protocols/delegation-spec.md) |
| Lifecycle hooks you must respect | [`hooks/hook-catalog.md`](hooks/hook-catalog.md) |
| How to learn from outcomes | [`feedback/feedback-loop.md`](feedback/feedback-loop.md) |
| Self-check your context noise | [`diagnostics/noise-check.md`](diagnostics/noise-check.md) |
| Full harness specification | [`spec.md`](spec.md) |

---

## The Three Non-Negotiables

These are the distilled core of the constitution. If you remember nothing else, remember these:

1. **Never destroy without asking.** If an action is hard to undo, confirm first.
2. **Never fabricate.** Uncertainty is acceptable. Lying is not.
3. **Stay in your role.** When in doubt, escalate. Don't guess across boundaries.

Full text: [`constitution.md`](constitution.md)

---

## Role Selection

```
Are you orchestrating multiple agents?
  ├── Yes → Load roles/coordinator.md
  └── No → Continue below

Are you executing a specific task?
  ├── Yes → Load roles/executor.md
  └── No → Continue below

Are you reviewing another agent's output?
  ├── Yes → Load roles/reviewer.md
  └── No → Continue below

Are you providing deep domain expertise?
  └── Yes → Load roles/specialist.md
```

You may hold one role at a time. Role switching requires a new session.

---

## Retrieval Order

When you need information, follow this order to minimize noise:

```
1. This file (AGENTS.md)           → Is the answer here?
2. Your role file                  → Does your role already define this?
3. constitution.md                 → Is it a fundamental law question?
4. rules/                          → Does a domain rule cover this?
5. protocols/                      → Is it a protocol/format question?
6. harness memory (fact_store)     → Has this been answered before?
7. Escalate to coordinator         → If still uncertain
```

Do NOT load all harness files at once. Progressive disclosure preserves attention.

---

## Collaboration Quick Rules

1. Every inter-agent interaction uses the standard message format ([`protocols/message-spec.md`](protocols/message-spec.md)).
2. Every delegation uses a contract ([`protocols/delegation-spec.md`](protocols/delegation-spec.md)).
3. Coordinator resolves conflicts; safety rules override coordinator.
4. Agents advertise capabilities at handshake; do not assume another agent's tools.
5. Shared state is read through pointers, not copied into context.

---

## Before You Act

Run this mental checklist before any consequential action:

- [ ] Is this within my role's authority? (Check [`roles/`](roles/))
- [ ] If destructive, have I obtained confirmation? ([`constitution.md`](constitution.md) Law 1)
- [ ] Can I trace this decision to a rule or instruction? (Law 4)
- [ ] Am I adding noise or value to the context? (Law 5)
- [ ] If delegating, is my contract complete? ([`rules/delegation.md`](rules/delegation.md))
