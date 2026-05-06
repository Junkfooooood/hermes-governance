# Hermes 三省六部制治理框架

> **版本:** v2.0 (2026-05-06)
> **状态:** 活跃开发中

---

## 一、架构总览

### 1.1 核心理念

Hermes 三省六部制是一个**多 Agent 协作治理框架**，灵感来源于中国古代的三省六部制度。核心思想是：

- **分权制衡**：决策、审核、执行分离
- **规则驱动**：所有行为受 harness 规则约束
- **可追溯**：每个决策都有审计轨迹
- **自治与监督平衡**：Agent 有自主权，但受统一治理

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户 (Human)                            │
│                    最终决策权 / Override                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   祖 Agent (Root Agent)                       │
│              统筹管理 / 全局记忆 / 协调三省                      │
└────────┬──────────────────┬──────────────────┬──────────────┘
         │                  │                  │
┌────────▼────────┐ ┌──────▼───────┐ ┌───────▼────────┐
│    中书省        │ │    门下省     │ │    尚书省       │
│  (Zhongshu)     │ │  (Menxia)    │ │  (Shangshu)    │
│   规划部门       │ │   审核部门    │ │   调度部门       │
│                 │ │              │ │                │
│  · 定义问题      │ │ · 方案审核    │ │ · 任务分解       │
│  · 收集信息      │ │ · 质量把关    │ │ · 任务分派       │
│  · 设计方案      │ │ · 批准/驳回   │ │ · 结果整合       │
└─────────────────┘ └──────────────┘ └───────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
            ┌───────▼───────┐ ┌─────────────▼─────────────┐ ┌───────▼───────┐
            │     工部       │ │          ...              │ │     兵部       │
            │   (Gongbu)    │ │    户部 / 礼部 / 刑部 / 吏部  │ │   (Bingbu)    │
            │   产出型       │ │                           │ │   自动化型     │
            │  代码/文件/内容 │ │    数据/表达/校验/治理      │ │  工具/工作流   │
            └───────────────┘ └───────────────────────────┘ └───────────────┘
```

### 1.3 通信约束

**六部之间禁止横向通信。所有流转必须经过尚书省。**

```
         尚书省 (唯一中枢)
        ↙  ↓  ↘
     工部  户部  兵部  ← 六部之间不直接联系
        ↖  ↑  ↗
         尚书省
```

原因：
- **清晰问责**：单一责任链
- **无协商循环**：不存在"你先来"的死锁
- **流程控制**：任务不会因横向通信变形
- **可审计**：单一路径可追溯

---

## 二、Harness 框架

### 2.1 什么是 Harness

Harness 是 Hermes Agent 的**操作系统**，它不是：
- 记忆系统（那是 AMS/mem0）
- 工具执行层（那是 hermes-agent）
- Prompt（那是 Agent 的指令层）

它是：
- 所有 Agent 必须遵守的**通用规则系统**
- 多 Agent 协作的**协议**
- 角色系统和**权限边界**
- 生命周期管理框架
- 质量和安全**执行层**

### 2.2 Harness 架构

```
┌──────────────────────────────────────────────┐
│                 CONSTITUTION                   │
│         (不可变, 所有 Agent, 始终生效)           │
├──────────────────────────────────────────────┤
│               ROLES (三省六部)                  │
│   (权限边界: 祖Agent → 三省 → 六部)              │
├──────────────────────────────────────────────┤
│              DOMAIN RULES                      │
│   (径向通信, 委派, 安全)                         │
├──────────────────────────────────────────────┤
│               PROTOCOLS                        │
│      (消息格式, 握手, 合同)                      │
├──────────────────────────────────────────────┤
│             HOOKS & LIFECYCLE                  │
│     (前置/后置动作, 常驻激活)                    │
├──────────────────────────────────────────────┤
│           FEEDBACK & DIAGNOSTICS               │
│        (学习循环, 噪声检查)                      │
└──────────────────────────────────────────────┘
```

下层可以更具体，但不能弱于上层。

### 2.3 宪法（7 条不可变法律）

| 法律 | 边界 | 内容 |
|------|------|------|
| **Law 1** | NEVER | 不执行破坏性操作（删除、drop、force-push 等），除非人类明确确认 |
| **Law 2** | NEVER | 不编造信息，不隐藏不确定性 |
| **Law 3** | ALWAYS | 遵守角色边界，不确定时升级，不猜测 |
| **Law 4** | ALWAYS | 重大决策必须可追溯（决策、依据、时间、权限） |
| **Law 5** | ALWAYS | 最小化上下文噪声，优先用指针而非全文 |
| **Law 6** | ALWAYS | 从现实中学习，记录结果，更新理解 |
| **Law 7** | ALWAYS | 委派时提供完整上下文，接收时验证假设 |

### 2.4 规则编译器

`harness_compiler.py` 实现三段式规则编译：

```
Extract → Normalize → Compile
  ↓          ↓          ↓
从 markdown   统一格式    按角色裁剪
抽取规则      分配 ID     注入 system prompt
```

**输入：**
- `harness/constitution.md`（宪法）
- `harness/rules/*.md`（领域规则）
- `harness/protocols/*.md`（协议）

**输出：**
- 带 `[rule_id]` 标记的规则文本
- 按角色裁剪（三省/产出型/自动化型/校验型/治理型）
- 支持 task overlay（write_code/read_only/external_api/deploy）

---

## 三、三省详解

### 3.1 中书省（Zhongshu Sheng — 规划部门）

**身份：**
- 角色：zhongshu
- 层级：department（三省）
- 权限：Plan
- 常驻：是

**职责：**
1. **定义问题** — 调用知识库，基于问题形成假设
2. **收集信息** — 调用工具收集额外信息验证假设
3. **设计方案** — 基于工作流，设计验证假设的动作 schema

**输出：**
```json
{
  "hypothesis": "...",
  "validation_actions": [...],
  "expected_results": [...],
  "workflow": "...",
  "required_resources": [...]
}
```

**边界：**
- 只规划，不执行、不审核、不调度
- 输出交付给门下省审核
- 被门下省打回时（≤3 轮），根据反馈修订方案

### 3.2 门下省（Menxia Sheng — 审核部门）

**身份：**
- 角色：menxia
- 层级：department（三省）
- 权限：Approve / Reject
- 常驻：是

**职责：**
1. **信息完整性检验** — 收集的信息是否完全
2. **方案范围调整** — 通过调整 schema 放大或缩小范围
3. **相似案例搜索** — 检索网络上是否有相似案例
4. **方案对比** — 给出不同方案的解决工作流
5. **缺失度判断** — 判断原方案的缺失程度

**决策矩阵：**

| 缺失程度 | 决策 | 说明 |
|---------|------|------|
| 高 | **REJECT** | 打回中书省，最多 3 轮，附具体反馈 |
| 可接受 | **APPROVE** | 交付尚书省，缺失范围在允许范围内 |

**两阶段审核：**
1. **Spec Compliance** — 方案是否符合需求
2. **Code Quality** — 可行性和工程质量

**边界：**
- 不执行具体任务
- 不直接联系六部
- 输出交付给尚书省

### 3.3 尚书省（Shangshu Sheng — 调度部门）

**身份：**
- 角色：shangshu
- 层级：department（三省）
- 权限：Delegate + Integrate
- 常驻：是

**职责（三重角色）：**

| 角色 | 说明 |
|------|------|
| **分发器** | 把大任务拆成小任务，按职责分给对应部门 |
| **裁判** | 判断六部交回的成果是否合格、是否返工 |
| **编排器** | 决定任务顺序、节奏、并行/串行关系 |

**核心流程：**
```
接任务 → 拆任务 → 派任务 → 收结果 → 验结果 → 再分派 → 整合输出
```

**输出：**
- **MD 文件** → 直接交付给用户
- **JSON 文件** → 给六部查看
- **工作流文件** → 给六部执行

**边界：**
- 是六部的唯一上级，六部之间禁止横向通信
- 不替六部干活，只负责调度和验收
- 所有跨部协调由尚书省统一处理

---

## 四、六部详解

### 4.1 工部（Gongbu — 产出型）

**职责：** 写代码、改文件、跑脚本、生成内容
**关注点：** 产出什么 (What)
**工具权限：** file, terminal

### 4.2 户部（Hubu — 数据型）

**职责：** 数据收集、资料搜索、知识库维护
**关注点：** 数据质量
**工具权限：** file, web

### 4.3 礼部（Libu — 表达型）

**职责：** 报告、总结、展示、翻译
**关注点：** 表达清晰
**工具权限：** file

### 4.4 兵部（Bingbu — 自动化型）

**职责：** 工具调用、浏览器自动化、工作流编排
**关注点：** 怎么跑起来 (How)
**工具权限：** terminal, file

**硬约束：**
- [bingbu.1] 只产出执行过程，不产出最终交付内容
- [bingbu.2] 只修改执行路径，不修改治理状态
- [bingbu.3] 结果聚合、状态迁移、完成判断必须由尚书省或吏部处理

### 4.5 刑部（Xingbu — 校验型）

**职责：** 权限检查、风险判断、错误检测、结果验证
**关注点：** 安全和可靠性
**工具权限：** file, terminal

**验证协议：**
- [xingbu.1] 执行合同中的成功标准检查
- [xingbu.2] 运行测试、安全扫描、验证
- [xingbu.3] 输出 JSON：`{"passed": true/false, "checks": [...], "issues": [...]}`
- [xingbu.4] 严格标准：部分通过 = 失败

### 4.6 吏部（Libu Renshi — 治理型）

**职责：** 状态跟踪、优先级管理、流程治理
**关注点：** 治理合规
**工具权限：** file

---

## 五、治理链（9 步流程）

### 5.1 完整流程

```
INTERVIEW → PLAN → REVIEW_SPEC → REVIEW_QUALITY → DECOMPOSE → DISPATCH → EXECUTE → VERIFY → INTEGRATE
   (中书省)  (中书省)   (门下省)      (门下省)       (尚书省)    (尚书省)    (六部)    (刑部)    (尚书省)
```

### 5.2 各阶段详解

| 阶段 | 执行者 | 输入 | 输出 | 说明 |
|------|--------|------|------|------|
| **INTERVIEW** | 中书省 | 用户需求 | questions, assumptions, clarity_score | 苏格拉底式提问，clarity ≥ 0.8 才进入规划 |
| **PLAN** | 中书省 | 需求 + 假设 | 执行方案 JSON | 设计验证假设的动作 schema |
| **REVIEW_SPEC** | 门下省 | 方案 | approve/reject/revise | spec compliance 审核 |
| **REVIEW_QUALITY** | 门下省 | 方案 | approve/revise | code quality 审核 |
| **DECOMPOSE** | 尚书省 | 方案 | 原子任务列表 | 拆解为 2-5 分钟任务，标注依赖 |
| **DISPATCH** | 尚书省 | 原子任务 | delegation contracts | 按职责分派给六部 |
| **EXECUTE** | 六部 | contracts | 执行结果 | 按依赖层级并行执行 |
| **VERIFY** | 刑部 | 执行结果 | passed/failed | 验证是否满足成功标准，失败重试最多 2 次 |
| **INTEGRATE** | 尚书省 | 全部结果 | 最终交付 | 整合结果 + 机械验证 + 记录决策 |

### 5.3 状态机

```python
class TransactionState(enum.Enum):
    CREATED = "created"
    INTERVIEW = "interview"
    INTERVIEW_COMPLETE = "interview_complete"
    PLAN = "plan"
    PLAN_COMPLETE = "plan_complete"
    REVIEW = "review"
    REVIEW_SPEC_COMPLETE = "review_spec_complete"
    REVIEW_QUALITY = "review_quality"
    REVIEW_QUALITY_COMPLETE = "review_quality_complete"
    DECOMPOSE = "decompose"
    DECOMPOSE_COMPLETE = "decompose_complete"
    DISPATCH = "dispatch"
    DISPATCH_COMPLETE = "dispatch_complete"
    EXECUTE = "execute"
    EXECUTE_COMPLETE = "execute_complete"
    VERIFY = "verify"
    VERIFY_COMPLETE = "verify_complete"
    INTEGRATE = "integrate"
    COMPLETE = "complete"
    REJECTED = "rejected"
    ERROR = "error"
```

---

## 六、联邦制架构（外部工具模式）

### 6.1 架构设计

将三省分别部署到独立的软件工具中，自主执行，通过文件协议与 Hermes 通信：

```
Hermes（丞相/中央政府）
  ├── 颁布 harness 规则
  ├── 分配任务
  ├── 检验成果
  └── 反馈修订

Codex（中书省）    Cursor（门下省）    Claude（尚书省）
  ├── 自主执行        ├── 自主审核        ├── 自主调度
  ├── 遵守 harness    ├── 遵守 harness    ├── 遵守 harness
  └── 提交成果        └── 提交批注        └── 提交整合结果
```

### 6.2 规则注入

Hermes 编译 harness 规则，生成三个配置文件：

```
~/.hermes/governance/deployments/
├── codex-instructions.md      # 中书省的完整规则
├── cursor-rules/              # 门下省的 .cursor/rules/
│   └── menxia.mdc
└── claude-instructions.md     # 尚书省的 CLAUDE.md
```

每个文件包含：
- 角色定义
- 行为边界
- harness 规则（宪法 7 条 + 角色特定规则）
- 输出格式要求（JSON schema）
- 成果提交方式

### 6.3 成果提交（文件协议）

每个 agent 完成后，写入共享目录：

```
~/.hermes/governance/submissions/
├── zhongshu/
│   └── 2026-05-06T10-30-00_plan.json
├── menxia/
│   └── 2026-05-06T10-35-00_review.json
└── shangshu/
    └── 2026-05-06T10-40-00_dispatch.json
```

### 6.4 工作流

```
1. 用户给 Hermes 一个任务
2. Hermes 编译规则，写入各工具配置
3. Hermes 通知中书省（或中书省轮询任务目录）
4. 中书省自主执行，写入 submissions/zhongshu/
5. Hermes 检验中书省成果
6. Hermes 通知门下省审核
7. 门下省自主审核，写入 submissions/menxia/
8. Hermes 检验门下省成果
9. Hermes 通知尚书省整合
10. 尚书省自主调度六部，写入 submissions/shangshu/
11. Hermes 最终验收
```

---

## 七、组件清单

### 7.1 核心插件（plugins/governance/）

| 文件 | 用途 |
|------|------|
| `state_machine.py` | 9 步治理链状态机 |
| `resident_manager.py` | Agent 生命周期管理（常驻身份+持久状态） |
| `harness_compiler.py` | 三段式规则编译器 |
| `rule_validator.py` | 机械验证器（检查 agent 输出合规性） |
| `feedback_tracker.py` | 规则有效性追踪（漂移报告+根因分析） |
| `cursor_proxy.py` | Cursor IDE 代理（间接调用 Claude Opus） |
| `event_bus.py` | 实时事件总线（JSONL 持久化） |
| `state_store.py` | 持久状态存储（乐观锁+崩溃恢复） |
| `ministry_router.py` | 可插拔任务路由（关键词/LLM 分类器） |
| `models.py` | 完整数据模型（13 个 dataclass） |
| `governance_tool.py` | 入口点 |
| `governance_hook.py` | Hook 集成 |

### 7.2 Harness 规则文件（harness/）

```
harness/
├── constitution.md          # 宪法（7 条不可变法律）
├── spec.md                  # Harness 规范
├── AGENTS.md                # Agent 总览
├── roles/                   # 角色定义
│   ├── zhongshu.md          # 中书省
│   ├── menxia.md            # 门下省
│   ├── shangshu.md          # 尚书省
│   ├── gongbu.md            # 工部
│   ├── hubu.md              # 户部
│   ├── libu.md              # 礼部
│   ├── bingbu.md            # 兵部
│   ├── xingbu.md            # 刑部
│   ├── libu-renshi.md       # 吏部
│   └── root-agent.md        # 祖 Agent
├── rules/                   # 领域规则
│   ├── safety.md            # 安全规则
│   ├── collaboration.md     # 协作规则
│   ├── communication.md     # 通信规则
│   ├── delegation.md        # 委派规则
│   ├── lifecycle.md         # 生命周期规则
│   └── quality.md           # 质量规则
├── protocols/               # 协议
│   ├── delegation-spec.md   # 委派规范
│   ├── handshake.md         # 握手协议
│   └── message-spec.md      # 消息规范
├── hooks/                   # Hook 目录
│   └── hook-catalog.md
├── diagnostics/             # 诊断
│   └── noise-check.md
└── feedback/                # 反馈
    └── feedback-loop.md
```

### 7.3 治理状态（governance/state/）

```
governance/state/
├── agents/                  # Agent 持久状态
│   ├── zhongshu.json
│   ├── menxia.json
│   ├── shangshu.json
│   └── ...
├── memory/                  # 结构化记忆
│   ├── boulder_state.json   # 项目状态跟踪
│   └── decision_log.json    # 决策历史
├── transactions/            # 治理链事务
│   └── txn_*.json
└── rule_feedback.jsonl      # 规则反馈日志
```

---

## 八、Agent 身份模型

### 8.1 三层层级

```
祖 Agent (Root)
  └── 三省 (Three Departments)
        └── 六部 (Six Ministries)
```

### 8.2 Agent 属性

| 属性 | 说明 |
|------|------|
| `agent_id` | 唯一标识符 |
| `tier` | root / department / ministry |
| `role` | root_agent / zhongshu / menxia / shangshu / gongbu / ... |
| `session_id` | 当前会话标识 |
| `capabilities` | 工具集和权限范围 |
| `parent_id` | 父 Agent |
| `resident` | 始终为 true（常驻角色） |

### 8.3 常驻 vs 按需

| 维度 | 按需（旧） | 常驻（当前） |
|------|-----------|-------------|
| 生命周期 | 创建 → 执行 → 销毁 | 永久，按任务激活 |
| 记忆 | 每次全新 | 跨任务积累经验 |
| 上下文 | 每次重新理解项目 | 持有持久上下文 |
| Token 成本 | 每次重新加载规则 | 规则已在 system prompt |

### 8.4 Agent 生命周期

```
IDLE (等待任务)
  → ACTIVATED (尚书省分派任务)
    → EXECUTE (执行领域工作)
      → REPORT (向尚书省汇报结果)
    → DEACTIVATE (回到空闲，保留记忆)
```

---

## 九、权限模型

### 9.1 权限层级

| 层级 | 范围 | 谁 |
|------|------|-----|
| **Override** | 覆盖任何规则 | 仅人类 |
| **Root** | 全部记忆，协调三省 | 祖 Agent |
| **Plan** | 设计方案，形成假设 | 中书省 |
| **Approve/Reject** | 验证，比较，决定 | 门下省 |
| **Delegate + Integrate** | 分派，监督，验证 | 尚书省 |
| **Execute (domain)** | 执行特定领域任务 | 六部 |
| **Read** | 读取文件，查询数据 | 所有 Agent 默认 |

### 9.2 升级路径

```
六部 不确定 → 尚书省 → 门下省 → 祖 Agent → 人类
```

每一级增加上下文。当上级可达时，不得猜测。

### 9.3 工具权限矩阵

| 角色 | terminal | file | web | browser | code_execution |
|------|----------|------|-----|---------|----------------|
| 中书省 | ✓ | ✓ | ✓ | - | - |
| 门下省 | - | ✓ | ✓ | - | - |
| 尚书省 | ✓ | ✓ | - | - | - |
| 工部 | ✓ | ✓ | - | - | - |
| 户部 | - | ✓ | ✓ | ✓ | - |
| 礼部 | - | ✓ | - | - | - |
| 兵部 | ✓ | ✓ | - | - | - |
| 刑部 | ✓ | ✓ | - | - | - |
| 吏部 | - | ✓ | - | - | - |

---

## 十、机械验证

### 10.1 验证器功能

`rule_validator.py` 实现机械验证：

1. **System Prompt 验证**
   - 检查宪法标记 `[law.1]` ~ `[law.7]`
   - 检查角色必需的规则类别
   - 检查 token 预算

2. **Agent 输出验证**
   - 兵部边界违规检测
   - 敏感信息泄露检测
   - 横向通信检测
   - 禁止工具使用检测
   - 合同范围违规检测

### 10.2 反馈追踪

`feedback_tracker.py` 记录 5 种反馈类型：

| 类型 | 说明 |
|------|------|
| `violation` | Agent 违反规则 |
| `compliance` | Agent 遵守所有规则 |
| `helpful_rule` | 规则帮助完成任务（正面信号） |
| `ignored_rule` | Agent 未遵守规则但非硬违规 |
| `confusing_rule` | 规则措辞不清，Agent 困惑 |

漂移报告包含根因分析：
- 单角色违规 → 可能是角色特定问题
- 多角色违规 → 规则可能太严格或措辞不清
- 同时被忽略和标记为困惑 → 需要重写规则

---

## 十一、结构化记忆

### 11.1 三层记忆

| 层 | 文件 | 说明 |
|----|------|------|
| **Boulder State** | `boulder_state.json` | 项目状态跟踪（活跃/阻塞/完成的目标） |
| **Decision Log** | `decision_log.json` | 决策历史（每次治理链的结果） |
| **Notepad Wisdom** | `notepad_wisdom.json` | 模式/陷阱/最佳实践 |

### 11.2 System Prompt 六层组装

```
Layer 1: 角色定义（harness/roles/*.md）
Layer 2: 宪法 + 角色规则 + 任务覆盖（编译后）
Layer 3: 任务约束（合同详情）
Layer 4: 结构化记忆（Boulder State, Decision Log, Notepad Wisdom）
Layer 5: 累积 agent 记忆（最近 5 条）
Layer 6: 输出约束（角色特定硬约束）
```

---

## 十二、待实现功能

### 12.1 动态选官机制

当某个模型/Provider 不可用时，自动递补：

- 候选池配置
- 健康检查
- 熔断器（900 秒冷却）
- 单模型灾备模式

### 12.2 监控面板

Governance Dashboard（正在重新设计）：
- 任务看板
- Agent 运行状态
- 实时事件推送
- 告警中心
- 审计回放

### 12.3 环境隔离

- 文件隔离：每个 Agent 独立工作目录
- 权限隔离：细粒度工具权限
- 记忆隔离：私有/共享/任务上下文包
- 容器隔离：Docker（远期）

---

## 附录 A：术语表

| 术语 | 说明 |
|------|------|
| 三省 | 中书省、门下省、尚书省（决策层） |
| 六部 | 工部、户部、礼部、兵部、刑部、吏部（执行层） |
| 祖 Agent | 顶层协调者，统筹管理三省六部 |
| Harness | Agent 的操作系统，规则和协议框架 |
| Constitution | 宪法，7 条不可变法律 |
| Governance Chain | 9 步治理流程 |
| Resident Agent | 常驻 Agent，跨任务持久 |
| Delegation Contract | 委派合同，任务的完整描述 |
| Boulder State | 项目状态跟踪 |
| Decision Log | 决策历史 |
| Notepad Wisdom | 模式/陷阱/最佳实践 |
| Mechanical Validation | 机械验证，基于规则标记的自动检查 |
| Drift Report | 漂移报告，规则有效性的根因分析 |
