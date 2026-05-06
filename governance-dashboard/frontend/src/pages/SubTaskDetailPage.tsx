import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchJSON } from "../lib/api";
import type { Transaction, SubTask, ExecutionResult } from "../lib/types";
import { getRoleLabel, getRoleDescription } from "../lib/states";
import StateWrapper from "../components/StateWrapper";
import StatusBadge from "../components/StatusBadge";

/* ── Workflow stage definitions (embedded) ─── */

interface WorkflowStageDef {
  id: string;
  label: string;
  agentRole: string;
  description: string;
}

const WORKFLOW_STAGES: WorkflowStageDef[] = [
  { id: "interview", label: "需求澄清", agentRole: "zhongshu", description: "中书省通过提问澄清需求" },
  { id: "plan", label: "制定方案", agentRole: "zhongshu", description: "中书省制定执行方案" },
  { id: "review_spec", label: "合规审核", agentRole: "menxia", description: "门下省审核方案合规性" },
  { id: "review_quality", label: "质量审核", agentRole: "menxia", description: "门下省审核方案质量" },
  { id: "decompose", label: "任务分解", agentRole: "shangshu", description: "尚书省拆解为原子任务" },
  { id: "dispatch", label: "任务派发", agentRole: "shangshu", description: "尚书省向六部派发合同" },
  { id: "execute", label: "并行执行", agentRole: "六部", description: "六部并行执行原子任务" },
  { id: "verify", label: "结果验证", agentRole: "xingbu", description: "刑部验证执行结果" },
  { id: "integrate", label: "结果整合", agentRole: "shangshu", description: "尚书省整合最终结果" },
];

const STATE_TO_STAGE: Record<string, string> = {
  created: "interview",
  interview: "interview",
  interview_complete: "interview",
  plan: "plan",
  plan_complete: "plan",
  review: "review_spec",
  review_spec_complete: "review_spec",
  review_quality: "review_quality",
  review_quality_complete: "review_quality",
  decompose: "decompose",
  decompose_complete: "decompose",
  dispatch: "dispatch",
  dispatch_complete: "dispatch",
  execute: "execute",
  execute_complete: "execute",
  verify: "verify",
  verify_complete: "verify",
  integrate: "integrate",
  complete: "integrate",
};

/* ── Page ──────────────────────────────────── */

export default function SubTaskDetailPage() {
  const { txnId, subId } = useParams<{ txnId: string; subId: string }>();
  const navigate = useNavigate();
  const [txn, setTxn] = useState<Transaction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!txnId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJSON<Transaction>(`/api/tasks/${txnId}`);
      setTxn(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [txnId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const subTask = txn?.sub_tasks.find((st) => st.id === subId);
  const result = txn?.results.find((r) => r.ministry === subTask?.ministry);
  const contract = txn?.contracts.find(
    (c: Record<string, unknown>) => c.ministry === subTask?.ministry
  );

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <button
          onClick={() => navigate("/tasks")}
          className="text-gray-400 hover:text-gray-600"
        >
          任务看板
        </button>
        <span className="text-gray-300">/</span>
        <button
          onClick={() => navigate(`/tasks/${txnId}`)}
          className="text-gray-400 hover:text-gray-600 truncate max-w-[200px]"
        >
          {txn?.goal?.slice(0, 40) ?? txnId}
        </button>
        <span className="text-gray-300">/</span>
        <span className="text-gray-700 font-medium truncate">
          {subTask?.task?.slice(0, 40) ?? subId}
        </span>
      </div>

      <StateWrapper
        loading={loading}
        error={error}
        empty={!txn || !subTask}
        emptyMessage="子任务不存在"
        onRetry={fetchData}
      >
        {txn && subTask && (
          <div className="space-y-4">
            {/* Sub-task header */}
            <SubTaskHeader
              subTask={subTask}
              result={result}
            />

            {/* Embedded governance workflow */}
            <WorkflowPanel
              currentState={txn.state}
              subTask={subTask}
              result={result}
            />

            {/* Two-column: agent activity + details */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 space-y-4">
                {/* Agent activity */}
                <AgentActivityCard
                  subTask={subTask}
                  contract={contract}
                  result={result}
                />

                {/* Execution result detail */}
                {result && <ResultDetailCard result={result} />}
              </div>

              {/* Right sidebar */}
              <div className="space-y-4">
                {/* Sub-task attributes */}
                <SubTaskAttributes subTask={subTask} result={result} />

                {/* Success criteria */}
                {subTask.success_criteria.length > 0 && (
                  <SuccessCriteriaCard
                    criteria={subTask.success_criteria}
                    passed={result?.status === "completed"}
                  />
                )}

                {/* Debug */}
                <DebugPanel
                  subTask={subTask}
                  contract={contract}
                  result={result}
                />
              </div>
            </div>
          </div>
        )}
      </StateWrapper>
    </div>
  );
}

/* ── Sub-task Header ──────────────────────── */

function SubTaskHeader({
  subTask,
  result,
}: {
  subTask: SubTask;
  result?: ExecutionResult;
}) {
  const status = result?.status ?? "pending";
  const statusConfig = {
    completed: {
      label: "已完成",
      color: "bg-green-100 text-green-800",
      dot: "bg-green-500",
    },
    failed: {
      label: "失败",
      color: "bg-red-100 text-red-800",
      dot: "bg-red-500",
    },
    skipped: {
      label: "已跳过",
      color: "bg-gray-100 text-gray-600",
      dot: "bg-gray-400",
    },
    pending: {
      label: "等待中",
      color: "bg-amber-100 text-amber-800",
      dot: "bg-amber-400",
    },
  };
  const sc = statusConfig[status as keyof typeof statusConfig] ?? statusConfig.pending;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full ${sc.color}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
              {sc.label}
            </span>
            <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
              {getRoleLabel(subTask.ministry)}
            </span>
          </div>
          <h2 className="text-base font-semibold text-gray-900 leading-snug">
            {subTask.task}
          </h2>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span className="font-mono">{subTask.id}</span>
            {subTask.estimated_minutes > 0 && (
              <span>预估: {subTask.estimated_minutes}分钟</span>
            )}
            {result?.attempts && result.attempts > 1 && (
              <span>重试 {result.attempts} 次</span>
            )}
          </div>
        </div>

        {/* Parent task link */}
        <button
          onClick={() => window.history.back()}
          className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1 shrink-0"
        >
          ← 返回上级任务
        </button>
      </div>
    </div>
  );
}

/* ── Embedded Governance Workflow ──────────── */

function WorkflowPanel({
  currentState,
  subTask,
  result,
}: {
  currentState: string;
  subTask: SubTask;
  result?: ExecutionResult;
}) {
  const activeStageId = STATE_TO_STAGE[currentState] ?? "";
  const activeIndex = WORKFLOW_STAGES.findIndex((s) => s.id === activeStageId);
  const isTerminal = ["complete", "rejected", "error"].includes(currentState);
  const subTaskStatus = result?.status ?? "pending";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-700 mb-4">
        治理工作流
      </h3>

      {/* Pipeline visualization */}
      <div className="flex items-center gap-1 overflow-x-auto pb-4">
        {WORKFLOW_STAGES.map((stage, i) => {
          const isActive = !isTerminal && i === activeIndex;
          const isPast = isTerminal || i < activeIndex;
          const isError = currentState === "error" && i === activeIndex;
          const isAgentStage =
            stage.agentRole === subTask.ministry ||
            (stage.agentRole === "六部" &&
              ["gongbu", "hubu", "libu", "bingbu", "xingbu", "libu-renshi"].includes(
                subTask.ministry
              ));

          return (
            <div key={stage.id} className="flex items-center">
              <div
                className={`relative flex flex-col items-center px-3 py-2 rounded-lg text-xs transition-all min-w-[80px] ${
                  isActive
                    ? "bg-blue-50 border-2 border-blue-300 shadow-sm"
                    : isPast
                      ? "bg-green-50 border border-green-200"
                      : isError
                        ? "bg-red-50 border border-red-200"
                        : "bg-gray-50 border border-gray-200"
                }`}
              >
                {/* Agent stage indicator */}
                {isAgentStage && (
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full border-2 border-white" />
                )}
                <span
                  className={`font-medium ${
                    isActive
                      ? "text-blue-700"
                      : isPast
                        ? "text-green-700"
                        : isError
                          ? "text-red-700"
                          : "text-gray-400"
                  }`}
                >
                  {stage.label}
                </span>
                <span className="text-[10px] text-gray-400 mt-0.5">
                  {getRoleLabel(stage.agentRole)}
                </span>
                {isActive && (
                  <span className="absolute -bottom-1 w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                )}
              </div>
              {i < WORKFLOW_STAGES.length - 1 && (
                <div
                  className={`w-3 h-px ${isPast ? "bg-green-300" : "bg-gray-200"}`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Sub-task status in workflow context */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">当前阶段:</span>
            <StatusBadge state={currentState} showDot />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">原子任务状态:</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                subTaskStatus === "completed"
                  ? "bg-green-100 text-green-700"
                  : subTaskStatus === "failed"
                    ? "bg-red-100 text-red-700"
                    : subTaskStatus === "skipped"
                      ? "bg-gray-100 text-gray-500"
                      : "bg-amber-100 text-amber-700"
              }`}
            >
              {subTaskStatus === "completed"
                ? "已完成"
                : subTaskStatus === "failed"
                  ? "执行失败"
                  : subTaskStatus === "skipped"
                    ? "已跳过"
                    : "等待执行"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Agent Activity Card ──────────────────── */

function AgentActivityCard({
  subTask,
  contract,
  result,
}: {
  subTask: SubTask;
  contract?: Record<string, unknown>;
  result?: ExecutionResult;
}) {
  const roleDesc = getRoleDescription(subTask.ministry);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-blue-500" />
        Agent 执行活动
      </h3>

      <div className="space-y-3">
        {/* Agent info */}
        <div className="flex items-center gap-3 p-3 bg-blue-50/50 border border-blue-100 rounded-lg">
          <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center text-sm">
            {getRoleLabel(subTask.ministry).charAt(0)}
          </div>
          <div>
            <div className="text-sm font-medium text-gray-800">
              {getRoleLabel(subTask.ministry)}
            </div>
            <div className="text-xs text-gray-500">{roleDesc}</div>
          </div>
          {result && (
            <span
              className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                result.status === "completed"
                  ? "bg-green-100 text-green-700"
                  : result.status === "failed"
                    ? "bg-red-100 text-red-700"
                    : "bg-gray-100 text-gray-500"
              }`}
            >
              {result.status === "completed"
                ? "执行完成"
                : result.status === "failed"
                  ? "执行失败"
                  : "等待中"}
            </span>
          )}
        </div>

        {/* Contract (delegation) */}
        {contract && (
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2">执行合同</div>
            <div className="space-y-1.5 text-sm">
              {(contract.delegation_id as string) && (
                <div className="flex justify-between">
                  <span className="text-gray-500">合同 ID</span>
                  <span className="text-gray-700 font-mono text-xs">
                    {contract.delegation_id as string}
                  </span>
                </div>
              )}
              {(contract.authority as string[])?.length > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-500">权限范围</span>
                  <span className="text-gray-700 text-xs">
                    {(contract.authority as string[]).join(", ")}
                  </span>
                </div>
              )}
              {(contract.deadline as string) && (
                <div className="flex justify-between">
                  <span className="text-gray-500">截止时间</span>
                  <span className="text-gray-700 text-xs">
                    {contract.deadline as string}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Result preview */}
        {result?.result && (
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2">执行结果预览</div>
            <p className="text-sm text-gray-700 line-clamp-4">
              {typeof result.result === "string"
                ? result.result
                : JSON.stringify(result.result).slice(0, 500)}
            </p>
          </div>
        )}

        {/* Error */}
        {result?.error && (
          <div className="border border-red-200 bg-red-50 rounded-lg p-3">
            <div className="text-xs text-red-600 font-medium mb-1">错误信息</div>
            <p className="text-sm text-red-700">{result.error}</p>
          </div>
        )}

        {/* No activity yet */}
        {!contract && !result && (
          <div className="text-sm text-gray-400 text-center py-4 bg-gray-50 rounded-lg">
            暂无执行活动 — 等待派发
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Result Detail Card ───────────────────── */

function ResultDetailCard({ result }: { result: ExecutionResult }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-700 mb-3">执行结果详情</h3>
      <div
        className={`rounded-lg p-4 ${
          result.status === "completed"
            ? "bg-green-50 border border-green-200"
            : result.status === "failed"
              ? "bg-red-50 border border-red-200"
              : "bg-gray-50 border border-gray-200"
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`text-sm font-semibold ${
              result.status === "completed"
                ? "text-green-800"
                : result.status === "failed"
                  ? "text-red-800"
                  : "text-gray-600"
            }`}
          >
            {result.status === "completed"
              ? "执行成功"
              : result.status === "failed"
                ? "执行失败"
                : "已跳过"}
          </span>
          {result.attempts && result.attempts > 1 && (
            <span className="text-xs text-gray-500">
              (第 {result.attempts} 次尝试)
            </span>
          )}
        </div>
        {result.result && (
          <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed mt-2">
            {typeof result.result === "string"
              ? result.result
              : JSON.stringify(result.result, null, 2)}
          </div>
        )}
        {result.error && (
          <p className="text-sm text-red-700 mt-2">{result.error}</p>
        )}
        {result.reason && (
          <p className="text-xs text-gray-500 mt-2">原因: {result.reason}</p>
        )}
      </div>
    </div>
  );
}

/* ── Sub-task Attributes Sidebar ──────────── */

function SubTaskAttributes({
  subTask,
  result,
}: {
  subTask: SubTask;
  result?: ExecutionResult;
}) {
  const status = result?.status ?? "pending";
  const attrs = [
    { label: "任务 ID", value: subTask.id, mono: true },
    { label: "负责角色", value: getRoleLabel(subTask.ministry) },
    {
      label: "预估时间",
      value:
        subTask.estimated_minutes > 0
          ? `${subTask.estimated_minutes} 分钟`
          : "—",
    },
    { label: "依赖任务", value: subTask.depends_on.length > 0 ? subTask.depends_on.join(", ") : "无" },
    {
      label: "执行状态",
      value:
        status === "completed"
          ? "已完成"
          : status === "failed"
            ? "失败"
            : status === "skipped"
              ? "已跳过"
              : "等待中",
    },
    { label: "尝试次数", value: String(result?.attempts ?? 0) },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">任务属性</h4>
      <div className="space-y-2">
        {attrs.map((a) => (
          <div key={a.label} className="flex justify-between text-sm">
            <span className="text-gray-400">{a.label}</span>
            <span
              className={`text-gray-700 ${a.mono ? "font-mono text-xs" : ""}`}
            >
              {a.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Success Criteria Card ────────────────── */

function SuccessCriteriaCard({
  criteria,
  passed,
}: {
  criteria: string[];
  passed: boolean;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">成功标准</h4>
      <ul className="space-y-2">
        {criteria.map((c, i) => (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span
              className={`mt-0.5 shrink-0 ${
                passed ? "text-green-500" : "text-gray-300"
              }`}
            >
              {passed ? "✓" : "○"}
            </span>
            <span className={passed ? "text-gray-500" : "text-gray-700"}>
              {c}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── Debug Panel ──────────────────────────── */

function DebugPanel({
  subTask,
  contract,
  result,
}: {
  subTask: SubTask;
  contract?: Record<string, unknown>;
  result?: ExecutionResult;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-white border border-gray-200 rounded-xl">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm text-gray-500 hover:text-gray-700"
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
        <div className="px-4 pb-4 border-t border-gray-100 pt-3">
          <pre className="text-[10px] text-gray-600 bg-gray-50 rounded-lg p-3 overflow-auto max-h-[32rem] font-mono leading-relaxed">
            {JSON.stringify({ sub_task: subTask, contract, result }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
