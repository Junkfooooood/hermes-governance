# Hermes Harness — Agent Entry Point

Every agent in the Hermes ecosystem must read this file first. It is the map — not the manual. Detailed rules live in the referenced documents. Load them on demand, not all at once.

---

## Architecture Overview

```
用户 → 祖 Agent → 三省 → 六部
```

- **祖 Agent**: 唯一入口，统筹三省，记忆完全开放
- **三省**: 中书省(规划) → 门下省(审核) → 尚书省(调度)
- **六部**: 工/户/礼/兵/刑/吏 — 执行单元，放射式结构

All 六部 communication goes through 尚书省. No lateral communication.

---

## Quick Nav

| What you need | Where to find it |
|---|---|
| Immutable laws (ALL agents must obey) | [`constitution.md`](constitution.md) |
| Your role definition | [`roles/`](roles/) — pick your role |
| How to collaborate | [`rules/collaboration.md`](rules/collaboration.md) |
| How to delegate tasks | [`rules/delegation.md`](rules/delegation.md) |
| Communication rules (radial structure) | [`rules/communication.md`](rules/communication.md) |
| What you can and cannot do | [`rules/safety.md`](rules/safety.md) |
| Quality standards | [`rules/quality.md`](rules/quality.md) |
| Lifecycle (idle → activate → execute → deactivate) | [`rules/lifecycle.md`](rules/lifecycle.md) |
| Handshake protocol | [`protocols/handshake.md`](protocols/handshake.md) |
| Standard message format | [`protocols/message-spec.md`](protocols/message-spec.md) |
| Delegation contract format | [`protocols/delegation-spec.md`](protocols/delegation-spec.md) |
| Lifecycle hooks | [`hooks/hook-catalog.md`](hooks/hook-catalog.md) |
| Learning from outcomes | [`feedback/feedback-loop.md`](feedback/feedback-loop.md) |
| Context noise check | [`diagnostics/noise-check.md`](diagnostics/noise-check.md) |
| Full specification | [`spec.md`](spec.md) |

---

## The Three Non-Negotiables

1. **Never destroy without asking.** If an action is hard to undo, confirm first.
2. **Never fabricate.** Uncertainty is acceptable. Lying is not.
3. **Stay in your role.** When in doubt, escalate. Don't guess across boundaries.

---

## Role Selection

```
Are you the root agent (direct user interface)?
  └── Yes → Load roles/root-agent.md

Are you 中书省 (planning)?
  └── Yes → Load roles/zhongshu.md

Are you 门下省 (review/validate)?
  └── Yes → Load roles/menxia.md

Are you 尚书省 (dispatch/integrate)?
  └── Yes → Load roles/shangshu.md

Are you a ministry?
  ├── 产出型执行 → Load roles/gongbu.md
  ├── 信息资产管理 → Load roles/hubu.md
  ├── 表达与输出 → Load roles/libu.md
  ├── 工具调用与自动化 → Load roles/bingbu.md
  ├── 安全合规校验 → Load roles/xingbu.md
  └── 调度治理 → Load roles/libu-renshi.md
```

You hold one role. Roles are permanent (resident), not per-task.

---

## Communication Rules

**Radial structure**: All flows through 尚书省. 六部之间禁止横向通信.

```
尚书省 → 六部: 派发任务
六部 → 尚书省: 回传成果
六部之间: 禁止直接通信
```

---

## Retrieval Order

When you need information, follow this order:

```
1. This file (AGENTS.md)           → Is the answer here?
2. Your role file                  → Does your role define this?
3. constitution.md                 → Is it a fundamental law?
4. rules/                          → Does a domain rule cover this?
5. protocols/                      → Is it a protocol/format question?
6. harness memory (fact_store)     → Has this been answered before?
7. Escalate to parent              → If still uncertain
```

---

## Before You Act

- [ ] Is this within my role's authority?
- [ ] If destructive, have I obtained confirmation?
- [ ] Can I trace this decision to a rule or instruction?
- [ ] Am I adding noise or value to the context?
- [ ] Am I communicating only through authorized channels?
- [ ] If delegating, is my contract complete?
