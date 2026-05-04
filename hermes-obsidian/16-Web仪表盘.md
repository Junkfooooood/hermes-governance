---
tags: [web, dashboard, react, vite]
---

# Web 仪表盘

> React 19 + Vite + Tailwind CSS 4 管理界面

## 概述

Web 仪表盘是 Hermes 的管理前端，提供 Session 管理、分析、日志、配置编辑等功能。基于 Nous Research UI 设计系统。

## 核心架构

```
web/src/
  ├── App.tsx           # 路由和布局
  ├── pages/            # 页面组件
  └── plugins/          # 插件系统
```

### 技术栈

- React 19 + TypeScript
- Vite (构建工具)
- Tailwind CSS 4
- `@nous-research/ui` 设计系统

## 实现原理

### 页面

| 页面 | 功能 |
|------|------|
| SessionsPage | Session 管理 |
| AnalyticsPage | 使用分析 |
| LogsPage | 日志查看器 |
| CronPage | 定时任务管理 |
| SkillsPage | 技能浏览器 |
| ConfigPage | 配置编辑器 |
| EnvPage | 环境变量 |
| DocsPage | 文档 |
| ChatPage | 嵌入式聊天 (dashboard --tui) |

### 开发架构

- Vite 开发服务器代理 `/api` 到 Python 后端 `http://127.0.0.1:9119`
- 自定义 `hermesDevToken` 插件从运行中的 dashboard 获取 session token
- 构建输出: `hermes_cli/web_dist/`
- Session 认证: `window.__HERMES_SESSION_TOKEN__` 注入 `index.html`
- 支持 i18n、主题切换、插件系统

## 依赖关系

- ← [[02-CLI命令系统]]: `hermes dashboard` 启动
- → [[01-Agent核心引擎]]: 通过 API 与 Agent 交互

## 源码入口

| 文件 | 说明 |
|------|------|
| `web/src/App.tsx` | 主应用 |
| `web/vite.config.ts` | Vite 配置 |
| `web/package.json` | 依赖 |
| `web/src/pages/` | 页面组件 |
