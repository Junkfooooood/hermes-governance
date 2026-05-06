import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { fetchJSON } from "../lib/api";
import type { Transaction, AuditEntry } from "../lib/types";
import { getStateInfo, getRoleLabel } from "../lib/states";
import StateWrapper from "../components/StateWrapper";
import StatusBadge from "../components/StatusBadge";
import Pipeline from "../components/Pipeline";

export default function TaskDetailPage() {
  const { txnId } = useParams<{ txnId: string }>();
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

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate("/tasks")}
        className="text-sm text-gray-400 hover:text-gray-600 flex items-center gap-1"
      >
        ← 返回任务列表
      </button>

      <StateWrapper
        loading={loading}
        error={error}
        empty={!txn}
        emptyMessage="任务不存在"
        onRetry={fetchData}
      >
        {txn && <TaskObservationView txn={txn} />}
      </StateWrapper>
    </div>
  );
}

/* ── Main observation view ────────────────── */

function TaskObservationView({ txn }: { txn: Transaction }) {
  return (
    <div className="space-y-4">
      {/* Header card */}
      <TaskHeader txn={txn} />

      {/* Pipeline */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">治理管道</h3>
        <Pipeline currentState={txn.state} />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-3 gap-4">
        {/* Left: main content */}
        <div className="col-span-2 space-y-4">
          {/* Interview summary */}
          {txn.interview && <InterviewCard interview={txn.interview} />}

          {/* Plan summary */}
          {txn.plan && <PlanCard plan={txn.plan} />}

          {/* Review results */}
          {(txn.spec_review || txn.quality_review) && (
            <ReviewCard spec={txn.spec_review} quality={txn.quality_review} />
          )}

          {/* Sub-tasks */}
          {txn.sub_tasks.length > 0 && (
            <SubTasksCard tasks={txn.sub_tasks} results={txn.results} txnId={txn.txn_id} />
          )}

          {/* Execution results */}
          {txn.results.length > 0 && <ResultsCard results={txn.results} />}

          {/* Verify result */}
          {txn.verify_result && <VerifyCard verify={txn.verify_result} />}

          {/* Integrated result */}
          {txn.integrated_result && (
            <IntegratedResultCard result={txn.integrated_result} />
          )}
        </div>

        {/* Right: sidebar */}
        <div className="space-y-4">
          {/* Task attributes */}
          <TaskAttributes txn={txn} />

          {/* Audit timeline */}
          {txn.audit_trail.length > 0 && (
            <AuditTimelineCard entries={txn.audit_trail} />
          )}

          {/* Debug */}
          <DebugPanel txn={txn} />
        </div>
      </div>
    </div>
  );
}

/* ── Header ───────────────────────────────── */

function TaskHeader({ txn }: { txn: Transaction }) {
  const info = getStateInfo(txn.state);
  const isActive = info.category === "active";

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 mb-2">
            <StatusBadge state={txn.state} showDot />
            <span className="text-xs text-gray-400">{info.description}</span>
          </div>
          <h2 className="text-base font-semibold text-gray-900 leading-snug">
            {txn.goal.length > 120 ? txn.goal.slice(0, 120) + "..." : txn.goal}
          </h2>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span className="font-mono">{txn.txn_id}</span>
            <span>优先级: {txn.priority}</span>
            <span>
              创建: {new Date(txn.created_at).toLocaleString("zh-CN")}
            </span>
            {txn.updated_at && (
              <span>
                更新: {new Date(txn.updated_at).toLocaleString("zh-CN")}
              </span>
            )}
          </div>
        </div>
        {isActive && (
          <div className="flex items-center gap-1.5 text-xs text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            运行中
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Interview Card ───────────────────────── */

function InterviewCard({ interview }: { interview: Record<string, unknown> }) {
  const questions = (interview.questions as string[]) || [];
  const assumptions = (interview.assumptions as string[]) || [];
  const score = (interview.clarity_score as number) || 0;

  return (
    <Card title="需求澄清" icon=" ">
      <div className="space-y-3">
        {questions.length > 0 && (
          <div>
            <div className="text-xs text-gray-400 mb-1.5">澄清问题</div>
            <ul className="space-y-1">
              {questions.map((q, i) => (
                <li key={i} className="text-sm text-gray-700 flex gap-2">
                  <span className="text-gray-300 shrink-0">{i + 1}.</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {assumptions.length > 0 && (
          <div>
            <div className="text-xs text-gray-400 mb-1.5">已确认假设</div>
            <ul className="space-y-1">
              {assumptions.map((a, i) => (
                <li key={i} className="text-sm text-gray-600 flex gap-2">
                  <span className="text-green-400 shrink-0">✓</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="flex items-center gap-2 pt-1">
          <span className="text-xs text-gray-400">清晰度评分:</span>
          <div className="flex-1 h-1.5 bg-gray-100 rounded-full max-w-32">
            <div
              className={`h-full rounded-full ${
                score >= 0.8
                  ? "bg-green-400"
                  : score >= 0.5
                    ? "bg-amber-400"
                    : "bg-red-400"
              }`}
              style={{ width: `${score * 100}%` }}
            />
          </div>
          <span className="text-xs font-mono text-gray-500">
            {(score * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </Card>
  );
}

/* ── Plan Card ────────────────────────────── */

function PlanCard({ plan }: { plan: Record<string, unknown> }) {
  const summary = (plan.summary as string) || "";
  const role = (plan.role as string) || "";

  return (
    <Card title="执行方案" icon=" ">
      {role && (
        <div className="text-xs text-gray-400 mb-2">
          制定者: {getRoleLabel(role)}
        </div>
      )}
      {summary ? (
        <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 rounded-lg p-4 max-h-64 overflow-auto">
          {summary}
        </div>
      ) : (
        <p className="text-sm text-gray-400">无方案内容</p>
      )}
    </Card>
  );
}

/* ── Review Card ──────────────────────────── */

function ReviewCard({
  spec,
  quality,
}: {
  spec: Record<string, unknown> | null;
  quality: Record<string, unknown> | null;
}) {
  return (
    <Card title="审核结果" icon=" ">
      <div className="space-y-3">
        {spec && <ReviewItem label="合规审核" data={spec} />}
        {quality && <ReviewItem label="质量审核" data={quality} />}
      </div>
    </Card>
  );
}

function ReviewItem({
  label,
  data,
}: {
  label: string;
  data: Record<string, unknown>;
}) {
  const verdict = (data.verdict as string) || "unknown";
  const notes = (data.notes as string) || "";
  const verdictColor =
    verdict === "approve"
      ? "bg-green-100 text-green-800"
      : verdict === "reject"
        ? "bg-red-100 text-red-800"
        : "bg-amber-100 text-amber-800";
  const verdictLabel =
    verdict === "approve" ? "通过" : verdict === "reject" ? "驳回" : "需修改";

  return (
    <div className="border border-gray-100 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span
          className={`text-xs px-1.5 py-0.5 rounded font-medium ${verdictColor}`}
        >
          {verdictLabel}
        </span>
      </div>
      {notes && <p className="text-sm text-gray-600 mt-1">{notes}</p>}
    </div>
  );
}

/* ── Sub-tasks Card ───────────────────────── */

function SubTasksCard({
  tasks,
  results,
  txnId,
}: {
  tasks: Transaction["sub_tasks"];
  results: Transaction["results"];
  txnId: string;
}) {
  const resultMap = new Map(results.map((r) => [r.ministry, r]));

  return (
    <Card title={`原子任务 (${tasks.length})`} icon=" ">
      <div className="space-y-2">
        {tasks.map((st) => {
          const result = resultMap.get(st.ministry);
          const status = result?.status ?? "pending";
          return (
            <Link
              key={st.id}
              to={`/tasks/${txnId}/sub/${st.id}`}
              className={`block border rounded-lg p-3 hover:shadow-sm transition-all cursor-pointer ${
                status === "completed"
                  ? "border-green-200 bg-green-50/50 hover:border-green-300"
                  : status === "failed"
                    ? "border-red-200 bg-red-50/50 hover:border-red-300"
                    : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-gray-900">{st.task}</p>
                    <span className="text-gray-300 text-xs shrink-0">→</span>
                  </div>
                  {st.success_criteria.length > 0 && (
                    <ul className="mt-1 space-y-0.5">
                      {st.success_criteria.map((c, i) => (
                        <li
                          key={i}
                          className="text-xs text-gray-500 flex gap-1"
                        >
                          <span className="text-gray-300">•</span> {c}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                    {getRoleLabel(st.ministry)}
                  </span>
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      status === "completed"
                        ? "bg-green-100 text-green-700"
                        : status === "failed"
                          ? "bg-red-100 text-red-700"
                          : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {status === "completed"
                      ? "完成"
                      : status === "failed"
                        ? "失败"
                        : "等待"}
                  </span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </Card>
  );
}

/* ── Results Card ─────────────────────────── */

function ResultsCard({ results }: { results: Transaction["results"] }) {
  return (
    <Card title="执行结果" icon=" ">
      <div className="space-y-2">
        {results.map((r, i) => (
          <div
            key={i}
            className={`border rounded-lg p-3 ${
              r.status === "completed"
                ? "border-green-200"
                : r.status === "failed"
                  ? "border-red-200"
                  : "border-gray-200"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">
                {getRoleLabel(r.ministry)}
              </span>
              <span
                className={`text-xs px-1.5 py-0.5 rounded ${
                  r.status === "completed"
                    ? "bg-green-100 text-green-700"
                    : r.status === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-600"
                }`}
              >
                {r.status === "completed" ? "完成" : r.status === "failed" ? "失败" : "跳过"}
              </span>
            </div>
            {r.result && (
              <p className="mt-1.5 text-sm text-gray-600 line-clamp-3">
                {typeof r.result === "string"
                  ? r.result
                  : JSON.stringify(r.result).slice(0, 200)}
              </p>
            )}
            {r.error && (
              <p className="mt-1.5 text-sm text-red-600">{r.error}</p>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ── Verify Card ──────────────────────────── */

function VerifyCard({ verify }: { verify: Record<string, unknown> }) {
  const passed = verify.passed as boolean;
  const issues = (verify.issues as string[]) || [];
  const checks = (verify.checks as Array<Record<string, unknown>>) || [];

  return (
    <Card title="验证结果" icon=" ">
      <div
        className={`rounded-lg p-3 ${
          passed ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`text-sm font-semibold ${passed ? "text-green-800" : "text-red-800"}`}
          >
            {passed ? "验证通过" : "验证未通过"}
          </span>
        </div>
        {issues.length > 0 && (
          <ul className="space-y-1">
            {issues.map((issue, i) => (
              <li key={i} className="text-sm text-red-700 flex gap-1">
                <span className="text-red-400">!</span> {issue}
              </li>
            ))}
          </ul>
        )}
        {checks.length > 0 && (
          <div className="mt-2 space-y-1">
            {checks.map((c, i) => (
              <div key={i} className="text-xs text-gray-600 flex gap-2">
                <span>{(c.passed as boolean) ? "✓" : "✗"}</span>
                <span>{(c.detail as string) || (c.task_id as string)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

/* ── Integrated Result Card ───────────────── */

function IntegratedResultCard({ result }: { result: string }) {
  return (
    <Card title="整合结果" icon=" ">
      <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto font-mono">
        {result}
      </div>
    </Card>
  );
}

/* ── Task Attributes Sidebar ──────────────── */

function TaskAttributes({ txn }: { txn: Transaction }) {
  const info = getStateInfo(txn.state);

  const attrs = [
    { label: "事务 ID", value: txn.txn_id, mono: true },
    { label: "优先级", value: txn.priority },
    { label: "状态", value: info.label },
    { label: "修订次数", value: String(txn.revision_count) },
    { label: "子任务数", value: String(txn.sub_tasks.length) },
    { label: "审核结论", value: txn.review_verdict ?? "—" },
    {
      label: "创建时间",
      value: new Date(txn.created_at).toLocaleString("zh-CN"),
    },
    {
      label: "更新时间",
      value: txn.updated_at
        ? new Date(txn.updated_at).toLocaleString("zh-CN")
        : "—",
    },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">任务属性</h4>
      <div className="space-y-2">
        {attrs.map((a) => (
          <div key={a.label} className="flex justify-between text-sm">
            <span className="text-gray-400">{a.label}</span>
            <span className={`text-gray-700 ${a.mono ? "font-mono text-xs" : ""}`}>
              {a.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Audit Timeline Sidebar ───────────────── */

function AuditTimelineCard({ entries }: { entries: AuditEntry[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (i: number) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  const ACTION_LABELS: Record<string, string> = {
    complete: "完成",
    approved: "审核通过",
    rejected: "驳回",
    revise: "需修改",
    error: "错误",
    retry: "重试",
    decomposed: "任务分解",
    plan_complete: "方案完成",
    verify_passed: "验证通过",
    verify_failed: "验证失败",
    all_completed: "全部完成",
    partial_success: "部分完成",
    dispatched: "已派发",
    parallel_level: "并行执行",
    rule_violations: "规则违反",
    boundary_violation: "越界",
  };

  const ACTION_DOT: Record<string, string> = {
    complete: "bg-green-500",
    approved: "bg-green-500",
    verify_passed: "bg-green-500",
    all_completed: "bg-green-500",
    rejected: "bg-red-500",
    error: "bg-red-500",
    verify_failed: "bg-red-500",
    revise: "bg-amber-500",
    retry: "bg-amber-500",
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <h4 className="text-sm font-medium text-gray-700 mb-3">
        审计记录 ({entries.length})
      </h4>
      <div className="relative">
        <div className="absolute left-[5px] top-2 bottom-2 w-px bg-gray-200" />
        <div className="space-y-3">
          {entries.map((entry, i) => {
            const dotColor = ACTION_DOT[entry.action] ?? "bg-gray-400";
            const label = ACTION_LABELS[entry.action] ?? entry.action;
            const isExpanded = expanded.has(i);
            const extraKeys = Object.keys(entry).filter(
              (k) => k !== "step" && k !== "action"
            );

            return (
              <div key={i} className="relative pl-5">
                <div
                  className={`absolute left-0 top-1 w-[11px] h-[11px] rounded-full border-2 border-white ${dotColor}`}
                />
                <div
                  className="cursor-pointer"
                  onClick={() => toggle(i)}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-gray-600">
                      {entry.step}
                    </span>
                    <span className="text-xs text-gray-400">·</span>
                    <span
                      className={`text-xs ${
                        entry.action === "error" || entry.action === "rejected"
                          ? "text-red-600"
                          : entry.action === "approved" || entry.action === "complete"
                            ? "text-green-600"
                            : "text-gray-500"
                      }`}
                    >
                      {label}
                    </span>
                  </div>
                  {isExpanded && extraKeys.length > 0 && (
                    <pre className="mt-1 text-[10px] text-gray-500 bg-gray-50 rounded p-1.5 overflow-x-auto font-mono">
                      {JSON.stringify(
                        Object.fromEntries(extraKeys.map((k) => [k, entry[k]])),
                        null,
                        1
                      )}
                    </pre>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ── Debug Panel ──────────────────────────── */

function DebugPanel({ txn }: { txn: Transaction }) {
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
            {JSON.stringify(txn, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

/* ── Reusable Card ────────────────────────── */

function Card({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
        {icon && <span>{icon}</span>}
        {title}
      </h3>
      {children}
    </div>
  );
}
