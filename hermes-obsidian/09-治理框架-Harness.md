---
tags: [governance, harness, constitution, roles, rules]
---

# 治理框架 — Harness

> 7 条不可变宪法 + 4 角色体系 + 规则/协议层

## 概述

Harness 是 Hermes 的多代理治理框架，定义了宪法（不可变法则）、角色（权限边界）、领域规则和通信协议。架构分层：CONSTITUTION → ROLES → RULES → PROTOCOLS → HOOKS → FEEDBACK。低层可以更具体但不能更弱。

## 核心架构

```
CONSTITUTION (不可变)
    ↓ 约束
ROLES (权限边界)
    ↓ 细化
DOMAIN RULES (领域规则)
    ↓ 实现
PROTOCOLS (通信协议)
    ↓ 驱动
HOOKS & LIFECYCLE
    ↓ 反馈
FEEDBACK & DIAGNOSTICS
```

## 实现原理

### 宪法 — 7 条不可变法则 (`harness/constitution.md`)

| # | 法则 | 类型 | 违反后果 |
|---|------|------|---------|
| 1 | **安全第一** | NEVER | Session 终止 + 事件记录；重复 → 角色降级为只读 |
| 2 | **真实性** | NEVER | 立即纠正 + 审计条目；模式 → 角色限制为仅验证 |
| 3 | **边界尊重** | ALWAYS | 记录 + 审查；重复 → 角色范围缩小 |
| 4 | **可追溯性** | ALWAYS | "30天后审查者能否从日志重建决策路径？" |
| 5 | **降噪音** | ALWAYS | >50% → 强制压缩；黄金空间膨胀 → 自动指针提取 |
| 6 | **从现实学习** | ALWAYS | 已知未纠正错误 → 信任降级 |
| 7 | **协作完整性** | ALWAYS | 不完整委派 → 被接收方拒绝 |

**修正程序**: 人工发起 + 人工确认 + 版本递增。代理**不得**提议、起草或执行宪法修正。

### 角色体系

架构从四角色（Coordinator/Executor/Reviewer/Specialist）演进为**祖 agent + 三省 + 六部**体系。详见 [[10-治理框架-三省六部]]。

#### 祖 agent（总入口）
- 权限: **Override**（除人类外最高）
- 职责: 接收用户指令 → 统筹三省 → 返回结果
- 记忆库权限完全开放

#### 三省（父 agent，授权驱动）

| 省 | 权限 | 核心模式 |
|---|------|---------|
| 中书省 | **Plan** | 问题→假设→验证动作 schema |
| 门下省 | **Approve/Reject** | 信息完整性 + 相似案例对比 + 缺失度判断（≤3轮打回） |
| 尚书省 | **Delegate + Integrate** | 唯一中枢：分发器 + 裁判 + 编排器 |

#### 六部（执行子 agent）

| 部 | 权限 | 核心关键词 |
|---|------|-----------|
| 工部 | Execute (产出) | "做出什么结果" |
| 户部 | Execute (数据) | "有什么资源可用" |
| 礼部 | Execute (表达) | "怎么呈现结果" |
| 兵部 | Execute (自动化) | "怎么把动作跑起来" |
| 刑部 | Execute (校验) | "有没有风险和错误" |
| 吏部 | Execute (治理) | "流程是否闭环" |

**放射式约束**: 六部之间禁止横向通信，所有流转必须经过尚书省。

### 领域规则 (`harness/rules/`)

| 规则文件 | 核心内容 |
|---------|---------|
| `collaboration.md` | 常驻角色发现，全部通过尚书省；辐射式通信；共享状态用指针不复制 |
| `delegation.md` | 委派链: 祖Agent→三省→六部；合同生命周期: DRAFT→DISPATCHED→ACKNOWLEDGED→IN_PROGRESS→COMPLETED→VERIFIED→ACCEPTED/REVISED/REJECTED |
| `safety.md` | 三类: ALWAYS / ASK FIRST / NEVER；六部特有安全职责；兵部外部工具权限检查 |
| `communication.md` | 辐射式架构；六部禁止横向通信；11种意图类型；路由规则表 |
| `quality.md` | 5 标准: 可验证/可追溯/显式/最小/正确；各部质量职责；"Stop and Fix" 规则 |
| `lifecycle.md` | 常驻生命周期: IDLE→ACTIVATED(30s)→EXECUTE(3轮)→REPORT(60s)→DEACTIVATE；Token预算治理 |

### 通信协议 (`harness/protocols/`)

#### 握手协议 (`handshake.md`)
```
尚书省 → DISPATCH → 六部 (IDLE→ACTIVATED)
六部 → load task context → ACK/QUERY → 尚书省
尚书省 → confirm → 六部 enters EXECUTE
```

DISPATCH 包含: delegation_id, task, success_criteria, context_scope, authority, deadline, result_format, ministry, token_budget

#### 消息规范 (`message-spec.md`)
YAML frontmatter + content body
必填: message_id, from, to, intent, priority, timestamp, trace_id
11 种意图: DELEGATE, PLAN, VERDICT, DISPATCH, REPORT, INTEGRATE, QUERY, RESPONSE, ALERT, ACK, HEARTBEAT
路由规则: 六部→六部 禁止，必须经过尚书省
4 优先级: critical(立即) / high(当前轮) / normal(2轮内) / low(尽力)

#### 委派合同 (`delegation-spec.md`)
必填: delegation_id, task, success_criteria(二元/可验证), context_scope(显式白名单), authority(白名单), deadline(硬停/可延长+50%), result_format, ministry(目标六部)
可选: token_budget, dependencies, priority

### AGENTS.md 入口

快速导航表链接所有 harness 文档。3 条不可违背:
1. 无确认不破坏
2. 不编造
3. 守住角色

检索顺序: AGENTS.md → role file → constitution → rules → protocols → harness memory → 升级

## 决策权限模型

```
Read < Execute < Delegate+Integrate < Approve/Reject < Plan < Root < Override (仅人类)
```

升级路径: 六部不确定 → 尚书省 → 门下省 → 祖 Agent → Human

## 合规状态

| 状态 | 说明 |
|------|------|
| Compliant | 正常 |
| Deviation Logged | 偏差已记录 |
| Violation | 违规 |
| Unreliable | 不可靠 |

## 依赖关系

- ← [[01-Agent核心引擎]]: AIAgent 遵循宪法和规则
- ← [[10-治理框架-三省六部]]: 三省六部是 Harness 的具体实现
- → [[05-工具系统]]: delegate_tool 实现委派

## 源码入口

| 文件 | 说明 |
|------|------|
| `harness/constitution.md` | 7 条不可变法则 |
| `harness/spec.md` | 完整规范 |
| `harness/AGENTS.md` | 入口和快速导航 |
| `harness/roles/root-agent.md` | 祖 Agent |
| `harness/roles/zhongshu.md` | 中书省 (规划) |
| `harness/roles/menxia.md` | 门下省 (审核) |
| `harness/roles/shangshu.md` | 尚书省 (调度) |
| `harness/roles/gongbu.md` | 工部 (产出型) |
| `harness/roles/hubu.md` | 户部 (数据型) |
| `harness/roles/libu.md` | 礼部 (表达型) |
| `harness/roles/bingbu.md` | 兵部 (自动化型) |
| `harness/roles/xingbu.md` | 刑部 (校验型) |
| `harness/roles/libu-renshi.md` | 吏部 (治理型) |
| `harness/rules/collaboration.md` | 协作规则 |
| `harness/rules/delegation.md` | 委派规则 |
| `harness/rules/safety.md` | 安全规则 |
| `harness/rules/communication.md` | 通信规则 |
| `harness/rules/quality.md` | 质量规则 |
| `harness/rules/lifecycle.md` | 生命周期规则 |
| `harness/protocols/handshake.md` | 握手协议 |
| `harness/protocols/message-spec.md` | 消息规范 |
| `harness/protocols/delegation-spec.md` | 委派合同 |
