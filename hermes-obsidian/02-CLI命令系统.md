---
tags: [cli, commands, interface]
---

# CLI 命令系统

> 用户与 Hermes 交互的主要入口

## 概述

CLI 系统基于 `argparse` 构建，支持 Profile 切换、交互式聊天、Setup Wizard、斜杠命令等功能。

## 核心架构

### 入口点

`hermes_cli/main.py` (374KB) — 定义 `hermes` 命令入口

Profile 支持：`hermes --profile/-p <name>` 在模块导入前设置 `HERMES_HOME`

### 命令注册 `COMMAND_REGISTRY`

`hermes_cli/commands.py` (line 59) — `CommandDef` 数据类列表

每个命令包含：name、aliases、handler、args_hint、subcommands、platform_gate（cli_only/gateway_only）

## 实现原理

### 可用命令

| 命令 | 功能 |
|------|------|
| `hermes` / `hermes chat` | 交互式聊天（默认） |
| `hermes setup` | 交互式 Setup Wizard |
| `hermes gateway [start\|stop\|status\|install]` | 网关服务管理 |
| `hermes config [edit\|set\|wizard]` | 配置管理 |
| `hermes doctor` | 依赖和配置诊断 |
| `hermes auth` | 认证管理 |
| `hermes tools` | 工具配置 |
| `hermes sessions browse` | 交互式 session 浏览器 |
| `hermes acp` | ACP 服务器（编辑器集成） |
| `hermes cron` | 定时任务管理 |
| `hermes update` / `hermes uninstall` | 更新/卸载 |
| `hermes honcho [setup\|status]` | Honcho AI 记忆集成 |

### 斜杠命令

在交互式聊天中可用：

| 类别 | 命令 |
|------|------|
| Session | `/new`, `/clear`, `/retry`, `/undo`, `/compress`, `/rollback` |
| 控制 | `/steer`, `/background`, `/queue` |
| 配置 | `/config`, `/model`, `/tools` |
| 信息 | `/help`, `/status`, `/sessions` |

### Setup Wizard

`hermes_cli/setup.py` — 模块化设计，每个部分可独立运行：

1. **Model & Provider** — 选择 AI 提供商和模型
2. **Terminal Backend** — local / Docker / Modal / SSH / Singularity / Daytona
3. **Agent Settings** — 迭代次数、压缩、session 重置
4. **Messaging Platforms** — Telegram / Discord / Slack / WhatsApp 等
5. **Tools** — TTS、网页搜索、图片生成、浏览器

## 数据流

```
用户输入命令
  ↓
main.py: argparse 解析
  ↓
--profile 设置 HERMES_HOME
  ↓
命令路由到 handler
  ↓
交互式执行 / 后台服务
```

## 依赖关系

- → [[03-配置系统]]: 读写 config.yaml
- → [[11-网关系统]]: gateway 子命令管理网关服务
- → [[05-工具系统]]: tools 子命令配置工具

## 源码入口

| 文件 | 关键位置 |
|------|---------|
| `hermes-agent/hermes_cli/main.py` | CLI 主入口 |
| `hermes-agent/hermes_cli/commands.py:59` | COMMAND_REGISTRY |
| `hermes-agent/hermes_cli/setup.py` | Setup Wizard |
| `hermes-agent/hermes_cli/config.py` | 配置管理 |
