import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTasks } from "../hooks/useTasks";
import StateWrapper from "../components/StateWrapper";
import StatusBadge from "../components/StatusBadge";
import SearchBar from "../components/SearchBar";
import { getRoleLabel } from "../lib/states";
import type { TaskSummary } from "../lib/types";

const STATE_FILTERS = [
  { value: "", label: "全部" },
  { value: "execute", label: "执行中" },
  { value: "complete", label: "已完成" },
  { value: "error", label: "失败" },
  { value: "rejected", label: "已驳回" },
];

const SORT_OPTIONS = [
  { value: "updated_at", label: "最近更新" },
  { value: "created_at", label: "创建时间" },
  { value: "sub_task_count", label: "子任务数" },
];

export default function TaskListPage() {
  const [stateFilter, setStateFilter] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("updated_at");
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const navigate = useNavigate();

  const { tasks, total, loading, error, refresh } = useTasks({
    state: stateFilter || undefined,
    search: search || undefined,
    sort,
    limit,
    offset,
  });

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">任务看板</h2>

      <div className="flex items-center gap-3">
        <SearchBar
          placeholder="搜索任务名或ID..."
          onSearch={(q) => { setSearch(q); setOffset(0); }}
          className="w-64"
        />
        <select
          value={stateFilter}
          onChange={(e) => { setStateFilter(e.target.value); setOffset(0); }}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-md"
        >
          {STATE_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>{f.label}</option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-md"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <StateWrapper
        loading={loading}
        error={error}
        empty={tasks.length === 0}
        emptyMessage="暂无任务"
        onRetry={refresh}
      >
        <div className="space-y-3">
          {tasks.map((t) => (
            <TaskFolderCard
              key={t.txn_id}
              task={t}
              onClick={() => navigate(`/tasks/${t.txn_id}`)}
            />
          ))}
        </div>

        {total > limit && (
          <div className="flex items-center justify-between mt-4">
            <span className="text-xs text-gray-400">
              共 {total} 条，第 {Math.floor(offset / limit) + 1} 页
            </span>
            <div className="flex gap-2">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
                className="px-3 py-1 text-xs border border-gray-200 rounded disabled:opacity-40"
              >上一页</button>
              <button
                disabled={offset + limit >= total}
                onClick={() => setOffset(offset + limit)}
                className="px-3 py-1 text-xs border border-gray-200 rounded disabled:opacity-40"
              >下一页</button>
            </div>
          </div>
        )}
      </StateWrapper>
    </div>
  );
}

/* ── Task Folder Card ─────────────────────── */

function TaskFolderCard({ task, onClick }: { task: TaskSummary; onClick: () => void }) {
  const subTasks = task.sub_tasks || [];
  const progress = task.sub_task_progress;
  const roles = task.involved_roles || [];
  const isError = task.state === "error";
  const hasSubTasks = subTasks.length > 0;

  return (
    <div
      onClick={onClick}
      className={`bg-white border rounded-xl px-5 py-4 cursor-pointer hover:shadow-md transition-all ${
        isError ? "border-red-200" : "border-gray-200"
      }`}
    >
      <div className="flex items-center gap-4">
        {/* Folder icon */}
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${
          hasSubTasks ? "bg-blue-50" : "bg-gray-50"
        }`}>
          {hasSubTasks ? " " : " "}
        </div>

        {/* Main info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-900 truncate">{task.goal}</p>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xs text-gray-400 font-mono">{task.txn_id}</span>
            <StatusBadge state={task.state} showDot />
          </div>
        </div>

        {/* Sub-task progress */}
        {hasSubTasks && progress && (
          <div className="flex items-center gap-2 shrink-0">
            <ProgressBar progress={progress} total={subTasks.length} />
            <span className="text-xs text-gray-500 whitespace-nowrap">
              {progress.completed}/{subTasks.length}
              {progress.failed > 0 && (
                <span className="text-red-500 ml-1">{progress.failed}失败</span>
              )}
            </span>
          </div>
        )}

        {/* Involved roles */}
        {roles.length > 0 && (
          <div className="flex gap-1 shrink-0">
            {roles.slice(0, 4).map((r) => (
              <span key={r} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                {getRoleLabel(r)}
              </span>
            ))}
          </div>
        )}

        {/* Arrow */}
        <span className="text-gray-300 text-sm shrink-0">→</span>
      </div>
    </div>
  );
}

function ProgressBar({ progress, total }: { progress: { completed: number; failed: number; pending: number }; total: number }) {
  const pct = Math.round((progress.completed / total) * 100);
  return (
    <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full ${progress.failed > 0 ? "bg-amber-400" : "bg-green-400"}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
