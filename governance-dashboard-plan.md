# 多大模型运行状态监控平台 — 实现方案 V3

## Context

基于 PRD（`hermes-obsidian/PRD：多大模型运行状态监控平台.md`）实现独立监控平台。
技术选型：FastAPI + Vite + React + TypeScript，端口 9200。

---

## 1. 平台边界与独立性

**原则**：Dashboard 是 Hermes 治理状态的**只读消费者**，不反向侵入核心逻辑。

| 层 | 归属 | 说明 |
|---|---|---|
| 状态文件 (`transactions/`, `agents/`, `memory/`) | Hermes 治理插件 | 唯一事实来源，Dashboard 只读 |
| 事件流 (`event_bus`) | 共享层 | 治理插件 emit，Dashboard subscribe |
| 索引缓存 (`index.json`) | Dashboard 后端 | **可丢弃缓存**，启动时从事实来源重建，运行时异步刷盘 |
| 标注数据 (`annotations.jsonl`) | Dashboard 独有 | 仅 Dashboard 读写 |
| 告警事件 (`alerts.jsonl`) | 规则引擎产生 | **只读**，规则触发时 append |
| 告警处理状态 (`alert_state.json`) | Dashboard 独有 | **可写**，ack/suppress/resolve 操作 |

**独立启动能力**：
- Dashboard 可独立启动，不依赖 Hermes 进程
- Hermes 未运行时：展示历史数据，实时事件为空
- Hermes 运行中时：实时事件通过 WebSocket 推送

---

## 2. 数据模型分层

### 2.1 唯一事实来源（Hermes 治理插件生产，Dashboard 只读）

| 数据 | 文件 | 主键 | 生产者 |
|------|------|------|--------|
| 事务 | `transactions/{txn_id}.json` | `txn_id` | state_machine |
| Agent 状态 | `agents/{role}.json` | `role` | resident_manager |
| 决策日志 | `memory/decision_log.json` | — | state_machine |
| 模式知识 | `memory/notepad_wisdom.json` | — | state_machine |
| 规则反馈 | `rule_feedback.jsonl` | — | feedback_tracker |
| Boulder 状态 | `memory/boulder_state.json` | — | state_machine |

**主键统一**：全站使用 `txn_id` 作为事务主键，不混用 `transaction_id` / `id`。

### 2.2 实时事件流（event_bus 生产，WebSocket 消费）

```json
{
  "event_id": "evt_<uuid8>",
  "global_seq": 42,
  "txn_id": "txn_abc123",
  "txn_seq": 3,
  "type": "state.transition",
  "payload": { ... },
  "created_at": "2026-05-04T10:32:01Z"
}
```

- `event_id`：全局唯一，客户端去重用
- `global_seq`：**进程内**单调递增（不跨重启持久化）。只保证同一次 Dashboard 生命周期内的顺序。跨重启后，补偿以"历史重建 + 新会话订阅"处理，不试图延续旧 seq。客户端重连时以 `global_seq` 为补发顺序依据，补偿阶段**先补历史再订阅实时流**。若历史补发与实时流边界发生重复，客户端以 `event_id` 去重为最终准则
- `txn_id`：关联事务
- `txn_seq`：单事务内递增序号

### 2.3 审计事件分层

| 层级 | 事件类型 | 说明 |
|------|----------|------|
| L1 状态变更 | `state.transition` | 状态机流转 |
| L2 决策节点 | `agent.decision` | 审核通过/拒绝/修订 |
| L3 工具调用 | `agent.tool_start`, `agent.tool_complete` | 工具执行 |
| L4 规则校验 | `validation.passed`, `validation.failed` | 机械验证 |
| L5 人工干预 | `human.intervention` | 人类确认 |
| L6 错误恢复 | `transaction.error`, `agent.retry` | 异常与重试 |

---

## 3. 索引与性能策略

`index.json` 定义为**可丢弃缓存**：

- 启动时从事实来源（`transactions/*.json`）全量重建（始终可重建，不依赖缓存文件）
- 运行时由事件驱动更新（零文件 I/O）
- 异步刷盘策略：每 30 秒或每 50 个事件刷一次（取先到者），使用原子写入（写 `.tmp` → `os.replace()`），刷盘失败仅 log warning，不影响运行
- 文件损坏或缺失 → 自动重建，不影响功能

```python
class TaskIndex:
    def __init__(self, state_dir: Path):
        self._index_path = state_dir / "index.json"
        self._tasks: Dict[str, TaskSummary] = {}
        self._global_seq: int = 0  # 最新已处理的 global_seq

    def rebuild_from_files(self) -> None:
        """启动时扫描事实来源重建索引。"""
        for f in (self._state_dir / "transactions").glob("*.json"):
            try:
                txn = json.loads(f.read_text())
                self._tasks[txn["txn_id"]] = self._extract_summary(txn)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Skip corrupt txn file {f.name}: {e}")
        self._recalc_stats()

    def on_event(self, event: dict) -> None:
        """运行时事件驱动更新。"""
        seq = event.get("global_seq", 0)
        if seq <= self._global_seq:
            return  # 去重
        self._global_seq = seq
        # 更新逻辑...

    # 排序字段白名单 + 明确升降序
    # 约束：(1) 所有排序字段必须在 TaskSummary 上存在 (2) 时间字段统一用数值型 epoch float
    # (3) sort 参数只接受白名单中的 key，非法值静默回退到默认排序
    _SORT_FIELDS = {
        "updated_at":   ("updated_at_ts", True),   # 降序
        "created_at":   ("created_at_ts", True),    # 降序
        "sub_task_count": ("sub_task_count", True),
    }

    def query(self, state=None, search=None, sort="updated_at", limit=20, offset=0):
        field, desc = self._SORT_FIELDS.get(sort, ("updated_at_ts", True))
        results = list(self._tasks.values())
        if state:
            results = [t for t in results if t.state == state]
        if search:
            q = search.lower()
            results = [t for t in results if q in t.goal.lower() or q in t.txn_id.lower()]
        results.sort(key=lambda t: getattr(t, field, 0), reverse=desc)
        return results[offset:offset+limit], len(results)
```

---

## 4. WebSocket 协议与容错

### 4.1 重连补偿（基于 global_seq）

```typescript
// 客户端重连后上报 last_global_seq
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "subscribe",
    last_global_seq: lastGlobalSeq,
  }));
};

// 服务端：先补历史，再订阅实时流（保证顺序）
@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    msg = await ws.receive_json()
    last_seq = msg.get("last_global_seq", 0)

    # 阶段 1：补发历史事件
    if last_seq > 0:
        missed = event_bus.get_events_after_seq(last_seq)
        for e in missed:
            await ws.send_text(json.dumps(e))

    # 阶段 2：订阅实时流（补发完成后才订阅，避免交错）
    queue = await event_bus.subscribe()
    try:
        while True:
            event = await queue.get()
            await ws.send_text(json.dumps(event, ensure_ascii=False))
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unsubscribe(queue)
```

### 4.2 去重

客户端按 `event_id` 去重（FIFO Set，上限 10000，超过时淘汰最旧条目）。页面切换时不清空（保持跨页面连续性），仅在 WebSocket 完全断开重建时重置。

### 4.3 鉴权配置

```python
# config.py
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
TOKEN_SOURCE = os.getenv("TOKEN_SOURCE", "env")  # env | file
TOKEN = os.getenv("DASHBOARD_TOKEN", "") if TOKEN_SOURCE == "env" else read_token_file()

def verify_token(token: Optional[str]) -> bool:
    if not AUTH_ENABLED:
        return True  # 开发模式自动放行
    return token == TOKEN
```

环境变量切换：
- `AUTH_ENABLED=false`：开发模式，无需 token
- `AUTH_ENABLED=true`：生产模式，需要 token
- `DASHBOARD_TOKEN=xxx`：设置 token

---

## 5. 统一 API 规范

**所有 REST API 统一返回**：

成功：
```json
{ "data": { ... }, "meta": { "request_id": "req_xxx", "timestamp": "..." } }
```

失败：
```json
{ "error": { "code": "TASK_NOT_FOUND", "message": "...", "details": {} }, "meta": { ... } }
```

HTTP 状态码与业务错误码映射：
| HTTP | 业务码 | 说明 |
|------|--------|------|
| 400 | `INVALID_PARAMS` | 参数校验失败 |
| 401 | `UNAUTHORIZED` | Token 无效 |
| 404 | `TASK_NOT_FOUND`, `AGENT_NOT_FOUND` | 资源不存在 |
| 500 | `INTERNAL_ERROR` | 服务端错误 |

前端同时检查 HTTP status 和 `error.code`：HTTP 非 2xx 时先走 HTTP 错误分支，再读 `error.code` 做细粒度处理。`meta.request_id` 在成功和失败响应中均返回。

前端统一处理：
```typescript
async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  const body = await res.json();
  if (!res.ok) throw new ApiError(body.error);
  return body.data;
}
```

---

## 6. 告警系统设计

### 6.1 告警事件（规则引擎产生，只读）

```json
// alerts.jsonl — append-only
{
  "alert_id": "alt_xxx",
  "rule_id": "alert.task_error",
  "severity": "critical",
  "txn_id": "txn_abc",
  "message": "任务 txn_abc 执行失败",
  "triggered_at": "..."
}
```

### 6.2 告警处理状态（Dashboard 写入）

```json
// alert_state.json — key: alert_id
{
  "alt_xxx": {
    "status": "acknowledged",     // active | acknowledged | suppressed | resolved
    "acknowledged_by": null,
    "acknowledged_at": null,
    "suppressed_until": null,
    "resolved_at": null
  }
}
```

查询时合并：告警事件 + 处理状态 → 完整告警视图。

状态流转规则：
- `active` → `acknowledged`（人工确认，表示已知悉，正在处理）
- `active` / `acknowledged` → `suppressed`（临时抑制，设置 `suppressed_until` 到期时间）
- suppressed 到期恢复：**查询时动态判断** `suppressed_until` 是否过期，过期则视为 `active`。后台定时任务可做状态落盘优化，但不作为唯一真相源，避免前后端短暂不一致
- `acknowledged` → `resolved`（问题已修复，告警关闭）
- `resolved` 不可回退（终态）
- 允许多次 ack（保留操作历史，记录 `acknowledged_by` 和 `acknowledged_at`）

### 6.3 告警规则配置

```python
ALERT_RULES = [
    {"id": "alert.task_error",    "severity": "critical", "source": "transaction.state == 'error'"},
    {"id": "alert.task_timeout",  "severity": "warning",  "source": "deadline < now && state not in terminal"},
    {"id": "alert.task_stuck",    "severity": "warning",  "source": "updated_at + 10min < now && state not in terminal"},
    {"id": "alert.rule_violation","severity": "high",      "source": "feedback.type == 'violation'"},
    {"id": "alert.verify_failed", "severity": "high",      "source": "audit.action == 'verify_failed'"},
]
```

---

## 7. 空态 / 加载态 / 错误态

```tsx
function StateWrapper({ loading, error, empty, children }) {
  if (loading) return <Skeleton className="h-32" />;
  if (error) return <ErrorCard message={error} onRetry={...} />;
  if (empty) return <EmptyCard message="暂无数据" />;
  return children;
}
```

JSON 解析容错：`load_transaction_safe()` 对 `JSONDecodeError` / `FileNotFoundError` 返回 None + 日志警告。

---

## 8. Pipeline 阶段定义

**后端权威 + 前端兜底（仅用于渲染，不参与业务判断）**：

当前阶段判断、进度计算始终以后端返回的 `txn.state` 为准，前端兜底映射仅在后端不可用时用于展示。

```python
# 后端：唯一真相源
PIPELINE_STAGES = [
    {"id": "interview",      "label": "Deep Interview", "agent": "zhongshu"},
    {"id": "plan",           "label": "规划",            "agent": "zhongshu"},
    {"id": "review_spec",    "label": "Spec 审核",       "agent": "menxia"},
    {"id": "review_quality", "label": "质量审核",         "agent": "menxia"},
    {"id": "decompose",      "label": "任务分解",         "agent": "shangshu"},
    {"id": "dispatch",       "label": "派发",            "agent": "shangshu"},
    {"id": "execute",        "label": "执行",            "agent": "六部"},
    {"id": "verify",         "label": "验证",            "agent": "xingbu"},
    {"id": "integrate",      "label": "整合",            "agent": "shangshu"},
]
```

```typescript
// 前端：优先从后端获取，失败时使用兜底
const DEFAULT_STAGES = [ /* 同上，硬编码兜底 */ ];

async function getStages() {
  try {
    return await fetchJSON("/api/pipeline/stages");
  } catch {
    return DEFAULT_STAGES;
  }
}
```

---

## 9. 标注系统

annotations.jsonl 中每条记录同时包含评论内容和处理状态，语义上明确分离：

```json
{
  "annotation_id": "ann_xxx",
  "txn_id": "txn_abc",
  "event_index": 5,
  "content": "这里工具调用参数有误",   // 用户输入的评论
  "status": "pending",                   // 处理状态：pending | confirmed | fixed | ignored
  "created_at": "...",
  "updated_at": "..."
}
```

- `content`：用户输入的文本评论（可编辑，保留 `updated_at` 记录修改时间）
- `status`：处理结果标签（可流转）
- `event_index`：只读，创建后不可修改
- 删除：支持软删除（`deleted: true`），不物理删除。默认查询不返回 `deleted=true`，审计页可通过 `include_deleted=true` 参数显式包含已删除项
- 修改历史：每次 PATCH 记录 `updated_at`，后续可扩展 `edit_history` 数组

---

## 10. 视觉风格

在 PRD"简洁克制、白底"基础上增加监控感：

| 区域 | 风格 |
|------|------|
| 整体 | 白底、卡片化、留白 |
| 顶栏 | 实时状态条（连接状态 + 最新事件时间 + 活跃任务数） |
| 日志区 | 等宽字体（JetBrains Mono）、浅灰底色分区、行号 |
| 状态标签 | 高对比色块（PRD §11.3 配色） |
| 告警区 | Critical 红色左边框 + 浅红底色 |
| Pipeline | 连接线 + 圆角节点，当前阶段脉冲动画 |
| 指标卡片 | 大号加粗数字 + 右上角小型趋势箭头（↑↓） |
| Agent 卡片 | 三省浅蓝底、六部浅绿底 |
| 异常聚焦 | 任务列表中异常行左侧红点标记 |

---

## 11. 项目结构

```
~/.hermes/governance-dashboard/
├── backend/
│   ├── main.py                    # FastAPI + CORS + 静态文件 serve
│   ├── config.py                  # AUTH_ENABLED, TOKEN, STATE_DIR, PORT
│   ├── models.py                  # Pydantic 响应模型
│   ├── routers/
│   │   ├── overview.py            # GET /api/overview
│   │   ├── tasks.py               # GET /api/tasks, GET /api/tasks/{txn_id}
│   │   ├── agents.py              # GET /api/agents, GET /api/agents/{role}
│   │   ├── pipeline.py            # GET /api/pipeline/stages
│   │   ├── alerts.py              # GET/POST /api/alerts
│   │   ├── audit.py               # GET /api/audit/transactions
│   │   ├── annotations.py         # GET/POST/PATCH /api/annotations
│   │   └── events.py              # WS /ws/events
│   ├── services/
│   │   ├── task_index.py          # 内存索引（可丢弃缓存，事件驱动）
│   │   ├── governance_bridge.py   # 读取 state_store 文件（带容错）
│   │   ├── alert_engine.py        # 告警规则引擎
│   │   └── event_bus.py           # 事件总线
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                # React Router
│   │   ├── lib/
│   │   │   ├── api.ts             # fetchJSON + 统一错误处理
│   │   │   ├── ws.ts              # WebSocket client + global_seq 重连 + event_id 去重
│   │   │   └── types.ts           # TS 类型
│   │   ├── hooks/
│   │   │   ├── useEvents.ts       # 实时事件 hook
│   │   │   ├── useTasks.ts        # 任务数据 hook
│   │   │   └── useAlerts.ts       # 告警数据 hook
│   │   ├── components/
│   │   │   ├── Layout.tsx         # 侧边栏 + 顶栏状态条
│   │   │   ├── StateWrapper.tsx   # 空态/加载态/错误态
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── Pipeline.tsx       # 后端驱动 + 前端兜底
│   │   │   ├── AgentCard.tsx
│   │   │   ├── LogStream.tsx      # 虚拟滚动日志
│   │   │   ├── Timeline.tsx
│   │   │   ├── MetricsCard.tsx    # 数字 + 趋势箭头
│   │   │   └── SearchBar.tsx
│   │   └── pages/
│   │       ├── OverviewPage.tsx
│   │       ├── TaskListPage.tsx
│   │       ├── TaskDetailPage.tsx
│   │       ├── AgentDetailPage.tsx
│   │       ├── AlertCenterPage.tsx
│   │       ├── AuditReplayPage.tsx
│   │       └── ConfigPage.tsx
│   └── tsconfig.json
└── start.sh
```

---

## 12. API 设计

所有响应统一 `{ data, meta }` 或 `{ error, meta }` 格式。

```
GET  /api/overview                                    → 总览统计
GET  /api/tasks?state=&search=&sort=&limit=&offset=   → 任务列表
GET  /api/tasks/{txn_id}                              → 任务详情
GET  /api/tasks/{txn_id}/audit                        → 审计记录（L1-L6 分层）
GET  /api/agents                                      → Agent 列表
GET  /api/agents/{role}                               → Agent 详情
GET  /api/pipeline/stages                             → Pipeline 阶段定义
GET  /api/alerts?status=&severity=&since=             → 告警列表
POST /api/alerts/{id}/ack                             → 确认告警
POST /api/alerts/{id}/suppress                        → 抑制告警
GET  /api/annotations?txn_id=                         → 标注列表
POST /api/annotations                                 → 创建标注
PATCH /api/annotations/{id}                           → 更新标注
WS   /ws/events?token=xxx                             → 实时事件流
```

---

## 13. 实现阶段

### Phase 1: 基础设施

1. 创建项目目录 + Vite/React/TS + FastAPI 骨架
2. Layout（侧边栏 6 导航 + 顶栏状态条）+ React Router
3. 统一 API 响应格式 + 错误中间件 + Pydantic 模型
4. `governance_bridge.py`（读取 state_store，JSON 解析容错）

### Phase 2: Event Bus + 实时管道（按顺序）

5. **先定义事件格式**：event_id + global_seq + txn_id + txn_seq + type + payload
6. **再做 emit**：`state_machine.advance()` emit 状态转换 + `resident_manager._run_agent()` 接入 4 个 AIAgent 回调
7. **再做后端订阅**：`event_bus.py`（内存队列 + JSONL 持久化 + global_seq 单调递增）+ WebSocket 端点 + 重连补偿
8. **最后接前端**：`ws.ts`（global_seq 重连 + event_id 去重 + 指数退避）+ `useEvents.ts`

### Phase 3: 总览 + 任务列表

9. `task_index.py`（内存索引 + 启动重建 + 事件驱动 + 排序白名单 + 异步刷盘）
10. `GET /api/overview` + `OverviewPage.tsx`
11. `GET /api/tasks` + `TaskListPage.tsx`（筛选/搜索/排序）
12. `StateWrapper` 组件

### Phase 4: 任务详情 + Agent 详情 + Pipeline

13. `GET /api/tasks/{txn_id}` + `TaskDetailPage.tsx`
14. `GET /api/agents/{role}` + `AgentDetailPage.tsx`
15. `Pipeline.tsx`（后端权威 + 前端兜底映射）

### Phase 5: 告警 + 审计 + 标注

16. `alert_engine.py` + `GET /api/alerts` + `AlertCenterPage.tsx`
17. **审计回放 MVP**：时间轴回放 + 节点展开 + 基础筛选（按事件类型）
18. 标注 CRUD + 标注 UI

### Phase 6: 收尾

19. 视觉打磨（监控感：状态条、红点聚焦、趋势箭头、脉冲动画）
20. `start.sh`（venv + 依赖检查 + 端口检查 + 前端构建 + 启动后端）

---

## 14. 启动脚本

```bash
#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=9200

# 1. 端口检查
if lsof -i :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Error: Port $PORT already in use"; exit 1
fi

# 2. 依赖检查
command -v node >/dev/null || { echo "Error: node not found"; exit 1; }
command -v python3 >/dev/null || { echo "Error: python3 not found"; exit 1; }

# 3. 后端虚拟环境
VENV="$DIR/backend/.venv"
if [ ! -d "$VENV" ]; then
  echo "Creating Python venv..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$DIR/backend/requirements.txt"
fi

# 4. 前端构建（如果需要）
# 注意：此逻辑仅用于开发/本地便利场景。生产部署应由 CI/CD 预构建前端，
# 或使用显式 `--build` 参数触发构建，避免自动判断带来的排障困难。
STAMP="$DIR/frontend/dist/.build.stamp"
NEED_BUILD=false
if [ ! -d "$DIR/frontend/dist" ] || [ ! -f "$STAMP" ]; then
  NEED_BUILD=true
elif find "$DIR/frontend/src" -name "*.tsx" -newer "$STAMP" -print -quit | grep -q .; then
  NEED_BUILD=true
fi
if [ "$NEED_BUILD" = true ]; then
  echo "Building frontend..."
  cd "$DIR/frontend" && npm install --silent && npm run build
  touch "$DIR/frontend/dist/.build.stamp"
fi

# 5. 启动
echo "Dashboard → http://localhost:$PORT"
cd "$DIR/backend"
"$VENV/bin/python" -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 15. 验收标准

### 功能验收

1. 总览页统计与 transactions/*.json 一致
2. 任务列表筛选/搜索/排序正常
3. 任务详情 Pipeline + 时间线 + audit_trail 完整
4. 实时日志 WebSocket 推送正常
5. 告警规则触发正确，ack 跨刷新持久
6. 标注 CRUD 正常
7. 审计回放时间轴 + 基础筛选正常

### 异常态验收

8. 任务不存在 → 404 + 友好提示
9. JSON 解析失败 → 跳过 + 日志警告
10. WebSocket 断线 → 自动重连 + global_seq 补拉
11. Hermes 未运行 → 展示历史数据，实时区为空
12. index.json 损坏 → 自动重建

### 性能验收

13. 100 个事务 → 总览页加载 < 500ms
14. 1000+ 日志 → 虚拟滚动不卡顿
15. WebSocket 重连 → 3 秒内恢复，无重复事件
16. 启动扫描 100 个 JSON 文件 → < 200ms
