---
tags: [agent, core, engine]
---

# Agent 核心引擎

> Hermes 的心脏 — 管理整个对话生命周期的主循环

## 概述

Agent 核心引擎位于 `run_agent.py`（658KB，约 16000 行），核心类 `AIAgent` 负责从用户消息到 LLM 调用到工具执行的完整循环。

## 核心架构

### AIAgent 类 (line 810)

构造函数接受约 60 个参数，涵盖：
- 模型配置（provider、model、base_url）
- 工具配置（toolsets、terminal backend）
- 回调（display consumers、interrupt events）
- 平台身份（platform、chat_id、user_id）
- Session 管理（session_id、checkpoint）

### API 模式自动检测 (line 975-1006)

根据 `provider` 和 `base_url` 自动选择 API 模式：

| 模式 | 触发条件 | 用途 |
|------|---------|------|
| `chat_completions` | 默认 OpenAI 兼容 | 大多数提供商 |
| `codex_responses` | GPT-5.x + 直连 OpenAI | OpenAI Responses API |
| `anthropic_messages` | Anthropic 提供商 | Claude 原生 API |
| `bedrock_converse` | AWS Bedrock | 企业级部署 |

### 迭代预算 (line 944)

`IterationBudget(max_iterations)` — 线程安全计数器，限制每次对话的 LLM 调用总数。子代理获得独立预算。

## 实现原理

### 主循环 `run_conversation()` (line 9225)

```
1. 预处理
   ├── 清理 surrogate 字符
   ├── 剥离泄漏的 <memory-context> 块
   ├── 重置重试计数器
   └── 恢复主运行时（如果上轮使用了降级）

2. 系统提示词缓存 (line 9399)
   ├── 首次构建 _build_system_prompt()
   ├── 缓存到 SQLite
   └── 后续 session 从 SQLite 加载（保留 Anthropic prefix cache）

3. 预检上下文压缩 (line 9447)
   ├── 估算总请求 token（含工具 schema）
   └── 超阈值时运行最多 3 轮压缩

4. 记忆预取 (line 9586)
   └── _memory_manager.prefetch_all(query) — 缓存结果注入每次 API 调用

5. 工具调用主循环 (line 9594)
   while (api_call_count < max_iterations
          and iteration_budget.remaining > 0):
       ├── 检查用户中断
       ├── 消耗迭代预算
       ├── 排空 /steer 消息
       ├── 构建 api_messages（注入记忆上下文）
       ├── 应用 Anthropic prompt caching 断点
       ├── 清理孤立 tool_call/tool_result
       ├── API 调用（优先流式）
       └── 处理响应：提取工具调用 → 执行 → 追加结果
```

### Prompt 构建 `_build_system_prompt()` (line 4472)

组装层次（从上到下）：

1. **Agent 身份** — SOUL.md 或 DEFAULT_AGENT_IDENTITY
2. **用户/网关系统消息**
3. **工具行为指导** — MEMORY_GUIDANCE, SKILLS_GUIDANCE
4. **工具使用强制** — 按模型族自动检测
5. **模型特定指导** — Google、OpenAI 特殊处理
6. **持久记忆** — MEMORY.md, USER.md
7. **外部记忆插件块**
8. **技能索引**
9. **上下文文件** — AGENTS.md, .cursorrules（含注入扫描）
10. **时间戳、模型信息、平台提示**

### 工具执行 (line 8219)

`_execute_tool_calls()` 支持两种模式：
- **串行**: 顺序执行每个工具调用
- **并发**: `ThreadPoolExecutor` 最多 8 workers

并发安全检测 `_should_parallelize_tool_batch()` (line 312)：
- 工具在 `_PARALLEL_SAFE_TOOLS` 白名单中
- 或路径作用域非重叠（如不同文件的读写）

## 数据流

```
用户输入
  ↓
run_conversation()
  ↓
_build_system_prompt() → system prompt
  ↓
_memory_manager.prefetch_all(query) → memory context
  ↓
LLM API call (via Transport 层)
  ↓
response.tool_calls[]
  ↓
_execute_tool_calls() → registry.dispatch()
  ↓
tool results → append to conversation
  ↓
(循环直到无工具调用或耗尽预算)
  ↓
_memory_manager.sync_turn() → 持久化记忆
```

## 配置项

```yaml
# config.yaml
agent:
  max_turns: 90              # 最大对话轮次
  api_max_retries: 3         # API 重试次数
  tool_use_enforcement: auto # 工具使用强制模式
  gateway_timeout: 1800      # 网关超时(秒)
  gateway_timeout_warning: 900
  gateway_notify_interval: 180
```

## 依赖关系

- → [[04-模型适配层]]: 通过 Transport 调用 LLM API
- → [[05-工具系统]]: 通过 ToolRegistry 执行工具
- → [[06-记忆系统-架构]]: 通过 MemoryManager 读写记忆
- → [[18-错误处理与容错]]: 重试、降级、凭证轮换
- ← [[11-网关系统]]: GatewayRunner 创建 AIAgent 实例

## 源码入口

| 文件 | 关键位置 |
|------|---------|
| `hermes-agent/run_agent.py:810` | AIAgent 类定义 |
| `hermes-agent/run_agent.py:9225` | run_conversation() 主循环 |
| `hermes-agent/run_agent.py:4472` | _build_system_prompt() |
| `hermes-agent/run_agent.py:8219` | _execute_tool_calls() |
| `hermes-agent/run_agent.py:214` | IterationBudget 类 |
| `hermes-agent/agent/prompt_builder.py:36` | Prompt 注入扫描 |
| `hermes-agent/agent/context_compressor.py` | 上下文压缩器 |
| `hermes-agent/agent/memory_manager.py` | 记忆管理器 |
