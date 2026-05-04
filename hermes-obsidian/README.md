---
tags: [readme, index]
---

# Hermes Agent 架构笔记库

> 基于 `~/.hermes` 项目的完整架构分析

## 使用方法

1. 用 Obsidian 打开 `~/.hermes/hermes-obsidian/` 作为 Vault
2. 打开 [[00-架构总览.canvas]] 查看交互式架构图
3. 点击笔记中的 `[[wikilink]]` 在模块间导航

## 笔记索引

### 架构总览
- [[00-架构总览]] — 项目概述和模块关系
- `00-架构总览.canvas` — 交互式架构图（Obsidian Canvas）

### 核心模块
- [[01-Agent核心引擎]] — 主循环、Prompt 构建、上下文压缩
- [[02-CLI命令系统]] — 交互式命令行、Setup Wizard
- [[03-配置系统]] — config.yaml、环境变量、分层合并
- [[04-模型适配层]] — Transport 抽象、15+ 提供商、凭证池
- [[05-工具系统]] — ToolRegistry、40+ 工具、并发执行

### 记忆系统
- [[06-记忆系统-架构]] — 五层生命周期、AMS 评分、新陈代谢、降噪音
- [[07-记忆系统-插件]] — ByteRover/Holographic/Mem0 等 8 个插件
- [[08-记忆系统-存储后端]] — Redis/Qdrant/Neo4j/AMS 四服务栈

### 治理框架
- [[09-治理框架-Harness]] — 7 条宪法、4 角色、6 组规则、3 种协议
- [[10-治理框架-三省六部]] — 中书省/门下省/尚书省 + 六部执行

### 辅助系统
- [[11-网关系统]] — 21 平台消息路由、Session 管理
- [[12-浏览器工具]] — CDP/Browserbase/Camofox 三后端
- [[13-技能系统]] — 渐进式披露、Skills Hub、自动合并淘汰
- [[14-MCP集成]] — Model Context Protocol 客户端
- [[15-语音系统]] — 7 TTS + 6 STT 提供商
- [[16-Web仪表盘]] — React 19 + Vite 管理界面
- [[17-RL训练系统]] — Atropos/Tinker 强化学习自进化
- [[18-错误处理与容错]] — 8 级分类、重试、降级
- [[19-部署架构]] — Docker 容器化部署
