---
tags: [mcp, protocol, integration]
---

# MCP 集成

> Model Context Protocol 客户端——外部工具扩展

## 概述

MCP（Model Context Protocol）客户端连接外部 MCP 服务器，发现其工具并注册到 Hermes 工具注册表。支持 stdio 和 HTTP/StreamableHTTP 传输。

## 核心架构

```
MCP Client (tools/mcp_tool.py)
  ├── stdio 传输 (子进程)
  ├── HTTP/StreamableHTTP 传输
  ├── 工具发现 → 注册到 ToolRegistry
  └── 后台事件循环 (_mcp_loop)
```

## 实现原理

### 连接方式

| 传输 | 说明 |
|------|------|
| stdio | 子进程通信，stderr → `~/.hermes/logs/mcp-stderr.log` |
| HTTP | REST API |
| StreamableHTTP | 流式 HTTP |

### 架构细节

- 后台守护线程运行专用事件循环 `_mcp_loop`
- 每个 MCP 服务器作为长期 asyncio Task 运行
- 工具调用通过 `run_coroutine_threadsafe()` 调度
- 线程安全: `_lock` 保护 `_servers` 和 `_mcp_loop`
- 自动重连: 指数退避，最多 5 次重试

### Sampling 支持

MCP 服务器可通过 `sampling/createMessage` 请求 LLM 补全

### 安全

- 错误消息中剥离凭证
- 每服务器可配置工具调用和连接超时

## 配置项

```yaml
# config.yaml
mcp_servers:
  my-server:
    command: npx
    args: ["-y", "@example/mcp-server"]
    env:
      API_KEY: ${MY_API_KEY}
  remote-server:
    url: https://mcp.example.com
    transport: streamable-http
```

## 依赖关系

- ← [[05-工具系统]]: MCP 工具注册为 `mcp-<server>` 前缀工具集
- ← [[01-Agent核心引擎]]: Agent 通过 handle_function_call() 调用 MCP 工具

## 源码入口

| 文件 | 说明 |
|------|------|
| `tools/mcp_tool.py` | MCP 客户端实现 |
