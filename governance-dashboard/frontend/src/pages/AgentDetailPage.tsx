import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchJSON } from "../lib/api";
import type { AgentState, AgentMemoryEntry, AgentTaskInvolvement } from "../lib/types";
import {
  getAgentLifecycle,
  getRoleLabel,
  getRoleDescription,
  getTierLabel,
} from "../lib/states";
import StateWrapper from "../components/StateWrapper";
import StatusBadge from "../components/StatusBadge";

export default function AgentDetailPage() {
  const { role } = useParams<{ role?: string }>();
  const navigate = useNavigate();
  const [agents, setAgents] = useState<AgentState[]>([]);
  const [selected, setSelected] = useState<AgentState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJSON<{ agents: AgentState[] }>("/api/agents");
      setAgents(data.agents);
      if (role) {
        const found = data.agents.find((a) => a.role === role);
        setSelected(found ?? null);
      } else if (data.agents.length > 0) {
        setSelected(data.agents[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSelect = (agent: AgentState) => {
    setSelected(agent);
    navigate(`/agents/${agent.role}`, { replace: true });
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Agent 运行状态</h2>

      <StateWrapper
        loading={loading}
        error={error}
        empty={agents.length === 0}
        emptyMessage="暂无 Agent 数据"
        onRetry={fetchData}
      >
        <div className="flex gap-4">
          {/* Left: Agent list */}
          <div className="w-48 shrink-0 space-y-1">
            {agents.map((a) => {
              const lc = getAgentLifecycle(a.lifecycle);
              const isSelected = selected?.role === a.role;
              const isMinistry = a.tier === "ministry";
              return (
                <button
                  key={a.role}
                  onClick={() => handleSelect(a)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    isSelected
                      ? isMinistry
                        ? "bg-blue-50 border border-blue-200 text-blue-900"
                        : "bg-emerald-50 border border-emerald-200 text-emerald-900"
                      : "hover:bg-gray-50 border border-transparent text-gray-700"
                  }`}
                >
                  <div className="font-medium">{getRoleLabel(a.role)}</div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        a.lifecycle === "execute" || a.lifecycle === "activated"
                          ? "bg-blue-500 animate-pulse"
                          : "bg-gray-300"
                      }`}
                    />
                    <span className={`text-xs ${lc.color}`}>{lc.label}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right: Agent detail */}
          {selected && (
            <div className="flex-1 space-y-4 min-w-0">
              <AgentSummaryCard agent={selected} />
              <AgentContextCard agent={selected} />
              <AgentTasksCard agent={selected} navigate={navigate} />
              <AgentTimeline agent={selected} />
              <AgentDebugPanel agent={selected} />
            </div>
          )}
        </div>
      </StateWrapper>
    </div>
  );
}

/* ── Layer 1: Runtime Summary ─────────────── */

function AgentSummaryCard({ agent }: { agent: AgentState }) {
  const lc = getAgentLifecycle(agent.lifecycle);
  const desc = getRoleDescription(agent.role);
  const isActive =
    agent.lifecycle === "execute" || agent.lifecycle === "activated";

  const lastMemory = agent.memory[agent.memory.length - 1];
  const failedCount = agent.memory.filter((m) => m.outcome === "failure").length;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-gray-900">
              {getRoleLabel(agent.role)}
            </h3>
            <span
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full ${
                isActive
                  ? "bg-blue-100 text-blue-800"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isActive ? "bg-blue-500 animate-pulse" : "bg-gray-400"
                }`}
              />
              {lc.label}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{desc}</p>
        </div>
        <span className="text-xs text-gray-400">{getTierLabel(agent.tier)}</span>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <MetricCell label="已完成任务" value={agent.total_tasks_completed} />
        <MetricCell label="Token 消耗" value={agent.total_tokens_consumed.toLocaleString()} />
        <MetricCell
          label="成功率"
          value={
            agent.total_tasks_completed > 0
              ? `${Math.round(((agent.total_tasks_completed - failedCount) / agent.total_tasks_completed) * 100)}%`
              : "—"
          }
          warn={failedCount > 0}
        />
        <MetricCell label="信任分" value={agent.trust_score.toFixed(1)} />
      </div>

      {lastMemory && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="text-xs text-gray-400 mb-1">最近活动</div>
          <div className="flex items-start gap-2">
            <span
              className={`mt-0.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                lastMemory.outcome === "failure" ? "bg-red-400" : "bg-green-400"
              }`}
            />
            <div className="min-w-0">
              <div className="text-sm text-gray-700 truncate">
                {lastMemory.summary || "(无输出)"}
              </div>
              <div className="text-xs text-gray-400 mt-0.5 font-mono">
                {lastMemory.contract_id} ·{" "}
                {new Date(lastMemory.timestamp).toLocaleString("zh-CN")}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Context Card: What is this agent doing NOW ── */

function AgentContextCard({ agent }: { agent: AgentState }) {
  const ctx = agent.current_context;
  const navigate = useNavigate();

  if (!ctx) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="text-sm text-gray-400 text-center">
          当前无任务上下文 — Agent 空闲
        </div>
      </div>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
      <div className="text-xs text-blue-600 font-medium mb-2">
        当前任务上下文
      </div>
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <div
            className="text-sm text-blue-900 font-medium cursor-pointer hover:underline"
            onClick={() => navigate(`/tasks/${ctx.txn_id}`)}
          >
            {ctx.goal}
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-xs text-blue-500 font-mono">{ctx.txn_id}</span>
            <StatusBadge state={ctx.stage} showDot />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Tasks Involvement Card ───────────────── */

function AgentTasksCard({
  agent,
  navigate,
}: {
  agent: AgentState;
  navigate: (path: string) => void;
}) {
  const tasks = agent.tasks_involved || [];

  if (tasks.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h4 className="text-sm font-medium text-gray-700 mb-3">运行任务详情</h4>
        <p className="text-sm text-gray-400 text-center py-4">暂无任务参与记录</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h4 className="text-sm font-medium text-gray-700 mb-4">
        运行任务详情 ({tasks.length}个任务)
      </h4>
      <div className="space-y-3">
        {tasks.map((t) => (
          <TaskInvolvementCard
            key={t.txn_id}
            task={t}
            agentRole={agent.role}
            onTxnClick={() => navigate(`/tasks/${t.txn_id}`)}
          />
        ))}
      </div>
    </div>
  );
}

function TaskInvolvementCard({
  task,
  agentRole,
  onTxnClick,
}: {
  task: AgentTaskInvolvement;
  agentRole: string;
  onTxnClick: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const statusConfig: Record<string, { label: string; color: string; dot: string }> = {
    active: { label: "执行中", color: "text-blue-700", dot: "bg-blue-500 animate-pulse" },
    completed: { label: "已完成", color: "text-green-700", dot: "bg-green-400" },
    pending: { label: "等待中", color: "text-amber-700", dot: "bg-amber-400" },
    failed: { label: "失败", color: "text-red-700", dot: "bg-red-400" },
    idle: { label: "空闲", color: "text-gray-500", dot: "bg-gray-300" },
  };
  const sc = statusConfig[task.agent_status] ?? statusConfig.idle;

  return (
    <div
      className={`border rounded-lg overflow-hidden ${
        task.agent_status === "active"
          ? "border-blue-200 bg-blue-50/30"
          : "border-gray-200"
      }`}
    >
      {/* Header */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <span className={`w-2 h-2 rounded-full shrink-0 ${sc.dot}`} />
        <div className="flex-1 min-w-0">
          <div
            className="text-sm text-gray-800 truncate cursor-pointer hover:underline"
            onClick={(e) => {
              e.stopPropagation();
              onTxnClick();
            }}
          >
            {task.goal}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-gray-400 font-mono">{task.txn_id}</span>
            <StatusBadge state={task.txn_state} />
            <span className={`text-xs ${sc.color}`}>{sc.label}</span>
          </div>
        </div>
        {task.sub_tasks.length > 0 && (
          <span className="text-xs text-gray-400">
            {task.sub_tasks.length}个原子任务
          </span>
        )}
        <span className="text-xs text-gray-400">{expanded ? "▲" : "▼"}</span>
      </div>

      {/* Expanded: sub-tasks this agent handles */}
      {expanded && task.sub_tasks.length > 0 && (
        <div className="border-t border-gray-100 px-4 py-3 bg-white">
          <div className="text-xs text-gray-400 mb-2">
            {getRoleLabel(agentRole)} 在此任务中的原子任务
          </div>
          <div className="space-y-1.5">
            {task.sub_tasks.map((st) => {
              const stStatus = st.status;
              const stStatusCfg = statusConfig[stStatus] ?? statusConfig.idle;
              return (
                <div
                  key={st.id}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-50"
                >
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${stStatusCfg.dot}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">{st.task}</p>
                    {st.success_criteria && st.success_criteria.length > 0 && (
                      <p className="text-xs text-gray-400 truncate mt-0.5">
                        {st.success_criteria[0]}
                      </p>
                    )}
                  </div>
                  <span className={`text-xs ${stStatusCfg.color}`}>
                    {stStatusCfg.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCell({
  label,
  value,
  warn,
}: {
  label: string;
  value: string | number;
  warn?: boolean;
}) {
  return (
    <div className="bg-gray-50 rounded-lg px-3 py-2.5">
      <div className="text-xs text-gray-400">{label}</div>
      <div
        className={`text-lg font-semibold mt-0.5 ${
          warn ? "text-red-600" : "text-gray-900"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

/* ── Layer 2: Narrative Timeline ──────────── */

function AgentTimeline({ agent }: { agent: AgentState }) {
  if (agent.memory.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h4 className="text-sm font-medium text-gray-700 mb-3">运行时间线</h4>
        <p className="text-sm text-gray-400 text-center py-6">暂无运行记录</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h4 className="text-sm font-medium text-gray-700 mb-4">运行时间线</h4>
      <div className="relative">
        <div className="absolute left-[7px] top-2 bottom-2 w-px bg-gray-200" />
        <div className="space-y-4">
          {[...agent.memory].reverse().map((entry, i) => (
            <TimelineEntry key={i} entry={entry} />
          ))}
        </div>
      </div>
    </div>
  );
}

function TimelineEntry({ entry }: { entry: AgentMemoryEntry }) {
  const [expanded, setExpanded] = useState(false);
  const isFailure = entry.outcome === "failure";
  const time = new Date(entry.timestamp).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const actionLabel = parseAction(entry.contract_id);

  return (
    <div className="relative pl-6">
      <div
        className={`absolute left-0 top-1 w-[15px] h-[15px] rounded-full border-2 border-white ${
          isFailure ? "bg-red-400" : "bg-green-400"
        }`}
      />
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-mono">{time}</span>
          <span
            className={`text-sm font-medium ${
              isFailure ? "text-red-700" : "text-gray-800"
            }`}
          >
            {actionLabel}
          </span>
          {isFailure && (
            <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
              失败
            </span>
          )}
        </div>
        {entry.summary && (
          <div className="mt-1">
            <p
              className={`text-sm ${isFailure ? "text-red-600" : "text-gray-600"} ${
                !expanded && entry.summary.length > 150 ? "line-clamp-2" : ""
              }`}
            >
              {entry.summary}
            </p>
            {entry.summary.length > 150 && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-xs text-blue-500 hover:text-blue-700 mt-1"
              >
                {expanded ? "收起" : "展开全文"}
              </button>
            )}
          </div>
        )}
        <div className="text-[10px] text-gray-400 font-mono mt-1">
          {entry.contract_id}
        </div>
      </div>
    </div>
  );
}

function parseAction(id: string): string {
  if (id.startsWith("interview_")) return "需求澄清";
  if (id.startsWith("plan_")) return "制定方案";
  if (id.startsWith("review_spec_")) return "合规审核";
  if (id.startsWith("review_quality_")) return "质量审核";
  if (id.startsWith("decompose_")) return "任务分解";
  if (id.startsWith("del_")) return "执行子任务";
  if (id.startsWith("verify_")) return "结果验证";
  return "处理任务";
}

/* ── Layer 3: Debug Raw Data ──────────────── */

function AgentDebugPanel({ agent }: { agent: AgentState }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-white border border-gray-200 rounded-xl">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 text-sm text-gray-500 hover:text-gray-700"
      >
        <span className="flex items-center gap-2">
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">
            JSON
          </span>
          原始数据
        </span>
        <span className="text-xs">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-5 pb-4 border-t border-gray-100 pt-3">
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-4 overflow-auto max-h-96 font-mono leading-relaxed">
            {JSON.stringify(agent, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
