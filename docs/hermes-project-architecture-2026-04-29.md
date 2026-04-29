# Hermes 项目整体架构分析文档

生成时间：2026-04-29 09:08:24 CST  
分析范围：`~/.hermes` 运行目录、`~/.hermes/hermes-agent` 项目源码、配置文件、harness、memory、skills、README/注释与当前会话上下文。  
安全说明：本文不记录任何 API Key、Token、密码等凭据；配置中的凭据统一视为 `[REDACTED]`。

---

## 0. 总览：三层架构如何组合成一个长期协作 Agent 系统

本项目不是单一聊天程序，而是由三层架构叠加形成的 Agent 操作系统：

```text
用户 / 微信 / CLI / 定时任务
        ↓
.hermes 主架构：配置、会话、工具、网关、运行时、项目规则
        ↓
主 Agent：理解任务、构建上下文、选择工具或治理流程
        ↓
三省六部制：复杂任务的计划 → 审核 → 调度 → 并行执行 → 整合
        ↓
工具层 / 文件系统 / 终端 / 浏览器 / Docker / 外部模型 / 微信接口 / 项目代码
        ↓
记忆系统：短期上下文、长期知识、用户偏好、技能沉淀、语义/图谱召回
        ↓
最终结果返回用户，并将高价值经验沉淀为记忆或技能
```

三者关系：

| 架构 | 核心角色 | 解决的问题 | 与其他架构的关系 |
|---|---|---|---|
| `.hermes` 主架构 | Agent 运行底座与控制面 | 如何接收任务、装载上下文、调用模型与工具、持久化会话、连接外部平台 | 承载三省六部制和记忆系统，是所有运行时配置与文件的入口 |
| 三省六部制多 Agent 架构 | 复杂任务治理与协作机制 | 如何把复杂任务拆解、审核、分派、并行执行、整合交付 | 作为 `.hermes` 工具层中的治理工具运行，并受 harness 与配置约束 |
| 记忆系统架构 | 长期连续性与低噪声知识系统 | 如何跨会话保留稳定信息、召回历史、沉淀 SOP、避免上下文污染 | 被 `.hermes` 在系统提示和每轮 prefetch 中读取；也为三省六部制提供历史和规则背景 |

---

# 一、`.hermes` 主架构

## 1. 核心定位

`.hermes` 是当前 Agent 系统的**主运行环境、配置中心、工具调度中心、上下文入口和长期状态目录**。它同时承担：

- **配置中心**：`config.yaml` 定义模型、provider、工具集、终端、浏览器、记忆、delegation、governance、platform toolsets、安全策略等。
- **运行底座**：`hermes-agent/` 是 Hermes Agent 源码，包含 CLI、gateway、核心 Agent loop、工具注册、记忆 provider、定时任务等。
- **上下文/规则入口**：`SOUL.md`、`memory.md`、`harness/`、`skills/` 在会话启动或任务执行时为 Agent 提供稳定规则和可复用能力。
- **状态存储**：`state.db`、`sessions/`、`cron/`、`memories/`、`memory/`、`fact_store/` 等保存会话、记忆、计划、定时任务和知识资产。
- **外部交互枢纽**：通过 terminal/file/browser/web/cron/send_message 等工具与本机、Docker、网页、模型 API、微信/Telegram/Discord 等平台连接。

一句话：`.hermes` 让 Agent 从“一个模型”变成“有配置、有工具、有会话、有治理、有记忆、有外部接口的操作系统”。

## 2. 核心功能

`.hermes` 主要解决五类问题：

1. **任务入口统一**：来自 CLI、微信、Discord、Telegram、cron 的任务都被转换为 Agent session 内的用户消息。
2. **上下文统一装配**：系统提示由身份、技能、项目规则、harness、memory snapshot、工具 schema、平台上下文共同构成。
3. **工具能力统一注册与调用**：`tools/registry.py` 管理工具 schema 与 handler；`model_tools.py` 触发工具发现；不同平台通过 toolsets 控制可用工具。
4. **执行循环统一**：`AIAgent._run_agent_loop()` 负责 LLM 调用、工具调用、工具结果回填、继续推理、最终输出、上下文压缩、会话持久化。
5. **状态与知识统一沉淀**：会话写入 SQLite/JSON，稳定事实写入 memory/skills/fact_store/向量库/图谱，经验写入 skill。

## 3. 内部模块

| 模块/文件/组件 | 作用 | 输入 | 输出 | 与其他模块的关系 |
|---|---|---|---|---|
| `~/.hermes/config.yaml` | 全局配置中心 | 用户配置、模型/provider、工具、安全、记忆、governance | 运行时参数 | 被 CLI、Agent、gateway、memory provider、governance loader 读取 |
| `~/.hermes/SOUL.md` | 核心原则与记忆路由锚点 | 稳定原则 | 极简核心提示 | 指向 `memory.md`、`memory/`、`fact_store/`、`skills/`、`byterover/`、`neo4j/`、`qdrant/` |
| `~/.hermes/memory.md` | 记忆地图 | 记忆层级说明 | 检索路径与治理规则 | 连接核心记忆、正文层、检索层、治理层 |
| `~/.hermes/hermes-agent/run_agent.py` | 核心 Agent loop | 用户消息、系统提示、工具 schema、历史消息 | 工具调用或最终回复 | 调用 prompt builder、model API、registry、memory manager、session store |
| `~/.hermes/hermes-agent/agent/prompt_builder.py` | 系统提示装配 | 身份、skills、context files、memory | system prompt | 把文件型规则和记忆注入 Agent |
| `~/.hermes/hermes-agent/agent/context_compressor.py` | 上下文压缩 | 过长会话历史 | 压缩摘要 | 防止上下文超限；可触发 memory provider 的 pre-compress hook |
| `~/.hermes/hermes-agent/tools/registry.py` | 工具注册与分发 | tool schema、handler | 可调用工具集合 | 所有工具自注册；模型工具调用经此分发 |
| `~/.hermes/hermes-agent/tools/terminal_tool.py` | 终端执行 | shell command | stdout/stderr/exit code | 与本机、Docker、git、构建工具、系统状态交互 |
| `~/.hermes/hermes-agent/tools/file_operations.py` | 文件读写搜索 patch | 路径、搜索词、patch | 文件内容/变更 | 支撑代码修改、文档生成、配置检查 |
| `~/.hermes/hermes-agent/tools/delegate_tool.py` | 子 Agent 派生 | 子任务、上下文、工具集 | 子 Agent 汇总结果 | 是通用 delegation；三省六部制是更强约束的治理式 delegation |
| `~/.hermes/hermes-agent/tools/governance_committee_tool.py` | 三省六部制工具 | 复杂任务、上下文、指定 ministries | JSON synthesis + audit trail | 读取 governance 配置和 harness role prompts，派生多个子 Agent |
| `~/.hermes/hermes-agent/gateway/` | 消息平台网关 | 微信/Telegram/Discord/Slack 等消息 | Agent 调用与平台回复 | 将外部平台消息路由到 Agent session |
| `~/.hermes/hermes-agent/cron/` | 定时任务系统 | cron job 配置 | 定时 Agent 执行结果 | 可向 origin/local/platform 投递结果 |
| `~/.hermes/hermes-agent/agent/memory_manager.py` | 记忆 provider 编排 | 内置记忆 + 外部 provider | prompt block、prefetch、memory tools | 连接 built-in memory 与 hermes 5-layer provider |
| `~/.hermes/memories/MEMORY.md` / `USER.md` | 内置轻量记忆 | 手工保存的稳定事实 | 启动时注入系统提示 | 有字符上限；中途写入不改变当前系统提示，下一会话生效 |
| `~/.hermes/skills/` | 可复用技能 | SOP、模板、工作流 | skill prompt/脚本/参考资料 | Agent 必须按相关性加载技能；复杂经验沉淀到此 |
| `~/.hermes/harness/` | 通用 Agent 宪法与协作规则 | 角色、规则、协议、生命周期 | 行为约束 | 约束所有 Agent；项目内 `hermes-agent/harness/` 是三省六部制专用入口 |

## 4. 功能实现逻辑链

```text
用户任务输入（微信/CLI/cron）
→ gateway 或 CLI 接收消息并定位 session
→ 读取 `config.yaml`：模型、provider、toolsets、memory、harness、platform 配置
→ prompt_builder 装配系统提示：SOUL、memory pointers、USER/MEMORY、skills、上下文文件、平台信息
→ MemoryManager 执行 prefetch：按当前问题召回相关记忆并用 `<memory-context>` 隔离注入
→ AIAgent 调用 LLM，携带工具 schema
→ 模型判断：直接回答，或发起 tool_calls
→ tools/registry 分发工具调用：文件、终端、浏览器、搜索、cron、delegate、governance 等
→ 工具结果追加到 conversation history
→ Agent 根据结果继续推理，必要时循环调用工具
→ 上下文接近阈值时 context_compressor 压缩历史
→ 任务完成后生成 final_response
→ 会话写入 state.db / sessions；工具轨迹写入日志
→ MemoryManager sync_turn / queue_prefetch；会话结束时可抽取长期记忆
→ gateway/CLI/平台把结果返回用户
```

## 5. 关键运行机制

### 5.1 任务解析机制

主 Agent 不直接等同于脚本执行器。它先通过 LLM 判断任务类型：

- 简单查询：直接回答或少量工具调用；
- 文件/代码/系统任务：调用 file/terminal/search/patch；
- 多步骤开发任务：可能使用 todo、delegate_task 或三省六部制；
- 高复杂度、多领域、需审查任务：调用 `governance_committee`。

### 5.2 上下文加载机制

上下文来源分层加载：

1. core prompt / developer rules；
2. `SOUL.md` 与 `memory.md` 指针；
3. `memories/MEMORY.md` 和 `USER.md` 快照；
4. 相关 skills；
5. 当前项目 AGENTS/CLAUDE/.cursorrules 等；
6. memory provider prefetch 召回；
7. 当前会话历史与工具结果。

设计重点是“低噪声”：核心文件只放指针，不放长正文；正文进入 `memory/`、`fact_store/`、`skills/`、向量库或图谱。

### 5.3 工具调用机制

工具文件自注册到 `registry`，并按 toolset 暴露给模型。平台可用工具由 `platform_toolsets` 控制。例如 CLI 使用 `hermes-cli`，消息平台使用各自 toolset。工具调用结果进入对话上下文，模型据此继续决策。

### 5.4 外部交互机制

- **模型**：通过 provider/base_url/model 配置调用 OpenAI-compatible 或特定 provider。
- **命令行/系统**：terminal tool 在本机或容器后端执行命令。
- **Docker**：通过 terminal 调用 docker/docker compose 或连接本地 Redis/Qdrant/Neo4j 服务。
- **微信等平台**：gateway/platform adapter 接收消息并返回结果。
- **项目代码**：file/search/patch/terminal 读写源码、运行测试、生成文档。
- **浏览器/网页**：browser/web tools 负责动态页面、网页提取与搜索。

### 5.5 异常处理机制

- 工具层捕获错误并以结构化结果返回给模型；
- memory provider 和 backend 多数失败采用 degrade gracefully，避免阻断主对话；
- governance pipeline 记录 phase error 和 audit trail；
- terminal 支持 background process 与通知，避免长任务阻塞；
- context compressor 防止上下文爆炸。

---

# 二、“三省六部制”多 Agent 协作架构

## 1. 核心定位

“三省六部制”是本项目面向复杂任务的**多 Agent 治理架构**。它不是普通并发 delegation，而是带有权力分立、强制审核、结构化交接、审计留痕和依赖感知执行的治理流水线。

其实现核心位于：

- `~/.hermes/hermes-agent/tools/governance_committee_tool.py`
- `~/.hermes/hermes-agent/hermes_cli/governance_config.py`
- `~/.hermes/hermes-agent/harness/AGENTS.md`
- `~/.hermes/hermes-agent/harness/constitution.md`
- `~/.hermes/hermes-agent/harness/roles/*.md`
- `~/.hermes/config.yaml` 的 `governance:` 配置段

## 2. 核心功能

它主要解决复杂任务中的五个问题：

1. **规划偏差**：中书省只负责规划，不执行、不审核自己。
2. **执行前质量控制**：门下省必须审核，拥有 `APPROVE / REVISE / REJECT` 权力。
3. **调度与执行分离**：尚书省负责把计划转成执行顺序，六部才执行。
4. **并行与依赖统一**：同 level ministries 并行，不同 level 顺序执行。
5. **可追溯性**：所有交接为 JSON artifact，所有状态转移写入 audit JSONL。

## 3. 内部模块

| 模块/文件/组件 | 作用 | 输入 | 输出 | 与其他模块的关系 |
|---|---|---|---|---|
| `governance_committee_tool.py` | 治理主状态机与工具 handler | `task`、`context`、可选 ministries | JSON final synthesis、DAG history、audit path | 注册为 `governance_committee` 工具；派生各角色子 Agent |
| `GovernanceDAG` | 确定性状态机 | 事件：started/plan/review/dispatch/execution/integration | 新 state、history | 保证流程只能按合法状态转换 |
| `GovernanceAuditLogger` | 审计日志 | transition、artifact、error | JSONL audit trail | 支撑复盘、调试、问责 |
| `governance_config.py` | 角色模型与凭据解析 | `config.yaml` governance 段、环境变量 | 每个角色的 provider/model/toolsets | 为每个子 Agent 注入不同模型和工具集 |
| `harness/constitution.md` | 不可变治理法 | 规则 | 权力分立、强制审核、JSON 交接、全程留痕等约束 | 所有治理角色必须遵守 |
| `harness/AGENTS.md` | 权限矩阵与入口 | 用户任务 | pipeline、communication rules、toolsets | 定义中书/门下/尚书/六部的边界 |
| `roles/zhongshu_sheng.md` | 中书省规划提示 | 用户任务、上下文 | plan JSON | 只规划，不执行、不审核、不调度 |
| `roles/menxia_sheng.md` | 门下省审核提示 | plan JSON | verdict JSON | 四维审核：可行性、完整性、风险、资源 |
| `roles/shangshu_sheng.md` | 尚书省调度/整合提示 | approved plan、execution results | dispatch JSON / synthesis JSON | 负责 dependency-aware execution_order 与最终整合 |
| `roles/liubu.md` | 六部执行提示 | subtask contract、success criteria | result JSON | 各 ministry 在边界内执行并验证 |
| `config.yaml/governance.departments` | 三省模型配置 | provider/model/toolsets | 角色运行参数 | 支持不同模型制衡 |
| `config.yaml/governance.ministries` | 六部模型配置 | provider/model/toolsets/enabled | execution role 参数 | 控制哪些部可用、并发上限与 fallback |

## 4. 功能实现逻辑链

```text
复杂任务进入主 Agent
→ 主 Agent 判断该任务需要结构化多 Agent 治理
→ 调用 `governance_committee(task, context)`
→ 初始化 GovernanceDAG：INIT → PLANNING
→ 中书省子 Agent 接收任务与上下文
→ 输出 plan JSON：任务复述、方案、分解、success criteria、dependencies、integration_strategy
→ 门下省子 Agent 审核 plan
    → APPROVE：进入 DISPATCHING
    → REVISE：带反馈回到中书省重新规划，最多 3 轮
    → REJECT：终止并返回拒绝原因
→ 尚书省子 Agent 将 approved plan 转为 dispatch JSON
    → assignments：每个 ministry 的任务合同
    → execution_order：按依赖分 level
→ 六部执行阶段
    → 每个 level 内 ministries 并行执行
    → level N+1 等待 level N 结果
    → 每个 ministry 只处理自己的 subtask，并返回 result JSON
→ 尚书省整合阶段
    → 汇总各 ministry 输出
    → 标记失败、冲突、未解决问题
    → 输出 synthesis JSON
→ governance_committee 返回 completed/partial/error、audit trail、DAG history
→ 主 Agent 根据 synthesis 生成用户可读最终结果
```

## 5. 关键运行机制

### 5.1 三省分权

- **中书省**：决策前规划层。负责拆任务、定义成功标准、识别依赖。
- **门下省**：监督/审核层。负责质量门禁，避免错误计划直接消耗执行资源。
- **尚书省**：调度/整合层。负责把计划变成可执行顺序，并在执行后整合结果。

三省不能互相越权，避免“自己计划、自己审核、自己执行”的偏差。

### 5.2 六部专责

| 部门 | 职能定位 | 典型任务 |
|---|---|---|
| 工部 `gongbu` | 实现/修复/开发 | 写代码、改文件、实现功能 |
| 刑部 `xingbu` | 测试/QA/验证 | 运行测试、复现、校验结果 |
| 礼部 `libu` | 文档/API/报告 | README、架构文档、说明文档 |
| 户部 `hubu` | 数据/研究/分析 | 数据处理、外部信息分析、报告 |
| 兵部 `bingbu` | 安全/合规 | 漏洞扫描、权限、风险审查 |
| 吏部 `libu_renshi` | 代码审查/质量 | review、规范、质量门禁 |

### 5.3 审核机制

门下省按四维审核：

1. 可行性：任务是否可由对应 ministries 执行；
2. 完整性：是否覆盖所有必要方面；
3. 风险：是否存在循环依赖、范围不清、成功标准模糊；
4. 资源：复杂度、部数量、整合策略是否合理。

审核结果是绑定 verdict。`REVISE` 会进入回路，`REJECT` 终止。

### 5.4 并行与依赖机制

尚书省输出 `execution_order`，例如：

```json
[["hubu", "libu"], ["gongbu"], ["xingbu", "libu_renshi"]]
```

含义：第一层并行研究与文档草案，第二层基于前置结果实现，第三层测试和审查。代码中使用 `ThreadPoolExecutor` 控制同层并行，`max_concurrent_ministries` 当前配置为 3。

### 5.5 结构化交接机制

所有阶段使用 JSON artifacts：

- plan artifact
- review verdict
- dispatch artifact
- ministry result
- synthesis artifact

这使多 Agent 协作可解析、可审计、可复盘，避免自由文本交接导致歧义。

### 5.6 审计与异常机制

每次 governance run 创建 JSONL audit trail，记录：

- state transition；
- phase_start；
- artifact；
- level_start / level_complete；
- error；
- governance_complete。

如果某个 ministry 失败，尚书省应显式报告 partial result，而不是隐藏失败。

---

# 三、记忆系统架构

## 1. 核心定位

记忆系统是 Hermes 从“单次对话执行者”升级为“长期项目协作者”的关键。它保存用户偏好、项目规则、长期知识、短期上下文、会话事实、技能 SOP、语义索引和关系图谱，并通过低噪声检索注入当前任务。

当前项目存在两条互补记忆路径：

1. **内置轻量记忆**：`~/.hermes/memories/MEMORY.md` 与 `USER.md`，通过 `memory` 工具维护，启动时作为快照注入。
2. **Hermes 5-layer provider**：`plugins/memory/hermes/`，使用 Redis + Qdrant + Neo4j + AMS，实现 working/short_term/long_term/core/archive 的检索、评分、路由和生命周期管理。

同时，文件型知识层还包括：

- `SOUL.md`、`memory.md`：核心指针；
- `memory/`：正文记忆；
- `fact_store/`：关键词/标签事实；
- `skills/`：可复用 SOP；
- `byterover/`：语义与时间线事件；
- `neo4j/`：图谱 schema 与查询；
- `qdrant/`：向量索引策略。

## 2. 核心功能

记忆系统保存内容类型：

| 类型 | 示例 | 推荐存储位置 |
|---|---|---|
| 用户偏好记忆 | 用户喜欢低噪声、核心记忆保持小而稳定 | `USER.md`、core/long_term |
| 项目长期记忆 | 架构原则、稳定配置、项目约定 | `MEMORY.md`、`memory/long_term/`、`fact_store/` |
| 任务过程记忆 | 当前任务状态、临时假设 | working / short_term，不进入 core |
| Agent 行为记忆 | 工具使用偏好、避坑经验 | `MEMORY.md` 或 skill |
| 工具调用记录 | 会话轨迹、terminal 输出、session logs | `state.db`、`sessions/`、工具日志 |
| 决策依据 | 方案选择、审查结论、投资 thesis | `memory/long_term/`、Neo4j、byterover |
| SOP / 经验沉淀 | 调试流程、研究流程、开发流程 | `skills/` |
| 语义召回内容 | “类似但关键词不同”的长期知识 | Qdrant |
| 关系/时间线 | 事件因果、thesis 演化、反馈链 | Neo4j / byterover |

## 3. 内部模块

| 模块/文件/组件 | 作用 | 输入 | 输出 | 与其他模块的关系 |
|---|---|---|---|---|
| `SOUL.md` | 核心原则、路由锚点 | 高置信稳定原则 | 极简 prompt anchor | 指向所有记忆层，要求 pointer-only |
| `memory.md` | 记忆地图 | 记忆层说明 | 检索顺序 | 告诉 Agent 先查什么、再查什么 |
| `memories/MEMORY.md` | Agent 个人笔记 | 环境事实、项目约定、工具 quirks | 启动注入的 memory block | 由 `memory` 工具 add/replace/remove 维护 |
| `memories/USER.md` | 用户画像 | 偏好、风格、长期目标 | 启动注入的 user profile | 帮助减少用户重复纠正 |
| `tools/memory_tool.py` | 内置记忆工具 | add/replace/remove | 写入 MEMORY/USER | 有字符上限、去重、文件锁、注入攻击扫描 |
| `agent/memory_manager.py` | 记忆 provider 编排 | built-in + external provider | system prompt block、prefetch、sync、tools | 统一调度记忆读写与工具暴露 |
| `agent/memory_provider.py` | provider 抽象接口 | lifecycle hooks | 插件标准 | 定义 initialize/prefetch/sync/on_session_end/on_memory_write |
| `plugins/memory/hermes/__init__.py` | 5-layer provider | 会话、配置、消息 | memory_search/status/score/approve_core | 连接 Redis、Qdrant、Neo4j、AMS |
| `plugins/memory/hermes/ams.py` | AMS 评分与路由 | candidate memory | 6 维评分、目标层 | 决定 discard/short_term/long_term/core |
| `plugins/memory/hermes/backends.py` | Redis/Qdrant/Neo4j 封装 | URL、查询、memory object | 存储/搜索结果 | Redis 管 metadata/FTS，Qdrant 管向量，Neo4j 管关系 |
| `plugins/memory/hermes/retrieval.py` | 多层召回级联 | query/session_id | recalled memories markdown | working → short_term → long_term → core → archive |
| `memory/memory-governance-spec.md` | 记忆治理规范 | 设计原则 | 层级、生命周期、噪声策略 | 约束什么该存、怎么升降级 |
| `memory/ams-engine.md` | AMS 设计文档 | 候选记忆 | 评分标准、路由矩阵 | 与 `ams.py` 实现对应 |
| `fact_store/` | 标签化事实库 | 稳定事实、模板、领域知识 | 可关键词检索事实 | 是 Qdrant/Neo4j 之前的低成本检索层 |
| `skills/` | 可复用操作知识 | 成功流程、脚本、模板 | skill prompt + linked files | 解决“怎么做”的过程记忆 |
| `byterover/` | 语义/时间线召回目录 | events、semantic index、timeline index | 历史事件与时间线 | 特别服务投资分析和事件演化 |
| `qdrant/` | 向量召回策略与服务入口 | embedding payload | semantic recall | 当前配置连接 `http://127.0.0.1:6333` |
| `neo4j/` | 图谱 schema/查询 | entity/event/thesis/decision/feedback | causality/timeline graph | 当前配置连接 `bolt://127.0.0.1:7687` |

## 4. 功能实现逻辑链

```text
用户与 Agent 交互
→ 当前 turn 开始
→ MemoryManager 调用各 provider 的 prefetch(query)
→ Hermes 5-layer retriever 按层召回：
    working 当前会话 Redis key
    → short_term Redis/RediSearch
    → long_term Qdrant vector + Redis enrichment
    → core Redis/core_candidate
    → archive Qdrant last resort
→ 召回结果格式化为 `## Recalled Memories`
→ MemoryManager 用 `<memory-context>` 包裹，标明“不是用户新输入”
→ Agent 基于当前问题 + recalled context 执行任务
→ 每轮结束 sync_turn：写入 working memory，供本会话后续召回
→ 显式 memory 工具写入时：
    写入 `MEMORY.md` / `USER.md`
    → on_memory_write 镜像到 Hermes provider
    → AMS 评分并路由到 short_term/long_term/core_candidate/archive
    → 可写 Redis metadata 和 Qdrant vector
→ 会话结束 on_session_end：
    从最近消息抽取 candidate memories
    → AMS 评分
    → route_memory 决定层级
    → Redis 保存 metadata
    → Qdrant 保存 embedding
    → 如有 relationships 写 Neo4j
    → 执行生命周期 promotion
    → 清理 working memory
```

## 5. 关键运行机制

### 5.1 记忆类型与生命周期

记忆层级：

```text
working → short_term → long_term → core
                         ↓
                      archive
```

- **working**：当前会话临时 turn 信息，Redis TTL，默认不长期保留；
- **short_term**：近期任务、临时假设，默认约 30 天 TTL；
- **long_term**：经过验证、可复用的知识；
- **core**：高稳定、高置信、长期影响行为的核心锚点；
- **archive**：过期、冲突、合并、废弃信息，默认不主动召回。

### 5.2 AMS 评分机制

AMS 使用六个维度：

| 维度 | 含义 |
|---|---|
| importance | 对核心目标的重要性 |
| stability | 是否长期稳定 |
| reuse | 未来复用概率 |
| time_sensitivity | 时间衰减速度，越高越 timeless |
| confidence | 可信度 |
| core_relevance | 与核心目标/身份/方法论相关性 |

当前权重：importance 0.25、stability 0.20、reuse 0.15、time_sensitivity 0.10、confidence 0.15、core_relevance 0.15。

路由矩阵：

| composite | stability | 目标层 |
|---|---|---|
| < 0.30 | 任意 | discard |
| 0.30–0.49 | 任意 | short_term |
| 0.50–0.79 | < 0.60 | short_term |
| 0.50–0.79 | ≥ 0.60 | long_term |
| ≥ 0.80 | < 0.80 | long_term |
| ≥ 0.80 | ≥ 0.80 | core / core_candidate |

### 5.3 低噪声机制

记忆系统通过以下方式避免污染：

- `SOUL.md` 和 `memory.md` 只放指针，不放长正文；
- `MEMORY.md` / `USER.md` 有字符上限；
- 内置 memory 工具拒绝重复项，写入前扫描 prompt injection/exfiltration 风险；
- 中途写入只落盘，不改变当前系统 prompt，避免破坏 prefix cache；
- recall 结果用 `<memory-context>` 隔离，防止模型误认为是用户新指令；
- archive/deprecated/merged 内容默认排除出主召回；
- skills 与 memory 分离：事实放 memory/fact_store，流程放 skills。

### 5.4 更新机制

记忆更新来自四个入口：

1. **显式 memory 工具**：用户偏好、稳定事实、环境约定；
2. **session end extraction**：会话结束时从最近消息自动抽取 candidate；
3. **pre-compress hook**：上下文压缩前提取即将丢弃消息中的高价值信息；
4. **skill_manage**：复杂流程成功后沉淀为 skill，而非塞进普通记忆。

### 5.5 服务后续任务机制

后续任务开始时，Agent 不需要用户重复说明全部背景：

- 用户偏好从 `USER.md` 注入；
- 项目约定从 `MEMORY.md` 和 `memory.md` 指针进入；
- 相关 SOP 从 `skills/` 加载；
- 类似历史从 `memory_search` / Qdrant 召回；
- 因果和时间线从 Neo4j/byterover 恢复；
- 会话历史可通过 `session_search` 查询。

因此，Agent 的角色从“只处理当前消息”变为“带着项目历史、用户偏好、工具经验和可追溯决策链持续协作”。

---

# 四、三层架构的端到端运行流程

## 1. 普通任务流程

```text
用户输入
→ `.hermes` gateway/CLI 接收
→ 主 Agent 加载配置、规则、记忆、skills
→ 判断任务简单或中等复杂
→ 直接调用工具：read/search/terminal/patch/browser/web 等
→ 验证结果
→ 必要时更新记忆或技能
→ 返回用户
```

## 2. 复杂任务流程

```text
用户输入复杂任务
→ 主 Agent 判断需要治理
→ 调用 governance_committee
→ 中书省计划
→ 门下省审核/修订
→ 尚书省调度
→ 六部按依赖分层并行执行
→ 尚书省整合
→ 主 Agent 转换为用户可读交付物
→ 关键经验进入 memory/skills
→ 返回用户
```

## 3. 长期学习流程

```text
任务执行
→ 观察结果和用户反馈
→ 判断是否是稳定偏好、项目规则、工具经验或可复用 SOP
→ 稳定事实写 memory
→ 操作流程写 skills
→ 关系/时间线写 Neo4j/byterover
→ 语义摘要写 Qdrant
→ AMS 定期促销/降级/归档
→ 后续任务按检索顺序低噪声召回
```

---

# 五、当前架构的开发与交接要点

## 1. 新开发者应优先理解的入口

1. `~/.hermes/config.yaml`：运行配置总入口；
2. `~/.hermes/hermes-agent/CONTRIBUTING.md`：项目源码结构与 core loop；
3. `~/.hermes/hermes-agent/run_agent.py`：主 Agent 执行循环；
4. `~/.hermes/hermes-agent/tools/registry.py`：工具注册与调用；
5. `~/.hermes/hermes-agent/agent/memory_manager.py`：记忆编排；
6. `~/.hermes/hermes-agent/tools/governance_committee_tool.py`：三省六部制实现；
7. `~/.hermes/SOUL.md` 与 `~/.hermes/memory.md`：低噪声记忆路由原则；
8. `~/.hermes/harness/` 与 `~/.hermes/hermes-agent/harness/`：通用 harness 与治理 harness。

## 2. 修改架构时的边界原则

- 不要把长正文写入 `SOUL.md` 或 `memory.md`；只放稳定指针。
- 不要把“怎么做”的流程写入普通 memory；应写成 skill。
- 不要绕过门下省审核直接让 ministries 执行复杂任务。
- 不要让一个治理子 Agent 同时规划、审核、执行。
- 不要让多个外部 memory provider 同时 active，避免工具 schema 膨胀和记忆冲突。
- 不要在架构文档或日志中暴露 API Key；统一 `[REDACTED]`。

## 3. 当前架构的优势

- 主运行底座、协作治理、长期记忆三层边界清晰；
- 复杂任务有强制审查和审计轨迹；
- 记忆系统强调低噪声、指针化、生命周期；
- 支持本机工具、Docker 服务、外部模型、消息平台、多 Agent 并行；
- 可将经验持续沉淀为 skills，减少重复劳动。

## 4. 当前潜在风险与改进方向

| 风险 | 说明 | 建议 |
|---|---|---|
| 配置复杂度高 | `config.yaml` 同时管理模型、工具、平台、记忆、governance | 增加配置分片或生成只读架构索引 |
| 多模型依赖 | 三省六部制依赖多个 provider；某个 provider 不可用会影响阶段 | 强化 fallback 与健康检查 |
| 记忆服务依赖本地 Docker | Redis/Qdrant/Neo4j/AMS API 停止会削弱 recall | 增加 doctor 检查与降级提示 |
| 上下文污染 | 大工具输出、base64、长日志可能进入会话 | 强化工具输出截断、trajectory 清理、压缩前抽取 |
| 技能重复 | skills 增长后可能重叠 | 定期 merge/deprecate，保持 active skills 精简 |
| 审计目录不完全一致 | config 中 `audit_dir` 与实现中 harness logs 路径需保持一致 | 后续统一 governance audit path 配置读取 |

---

# 六、简版结论

`.hermes` 是整个系统的运行底座：它负责配置、上下文、工具、会话、网关和状态；三省六部制是复杂任务的治理层：它负责计划、审核、调度、执行与整合；记忆系统是长期协作层：它负责把用户偏好、项目知识、任务经验和 SOP 以低噪声方式保存、召回和更新。

三者共同形成闭环：

```text
接收任务
→ 加载低噪声上下文和记忆
→ 判断任务复杂度
→ 简单任务直接工具执行，复杂任务进入三省六部制
→ 产出结果并验证
→ 将稳定知识写入 memory，将流程经验写入 skills
→ 下一次任务通过检索和上下文注入复用历史
```

这正是本项目从“聊天助手”走向“可持续开发与交接的长期 Agent 系统”的核心架构。
