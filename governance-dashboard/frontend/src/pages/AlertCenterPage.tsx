import { useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import StateWrapper from "../components/StateWrapper";
import type { Alert } from "../lib/types";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "border-l-red-500 bg-red-50",
  high: "border-l-orange-500 bg-orange-50",
  warning: "border-l-amber-500 bg-amber-50",
  info: "border-l-blue-500 bg-blue-50",
};

const STATUS_LABELS: Record<string, string> = {
  active: "活跃",
  acknowledged: "已确认",
  suppressed: "已抑制",
  resolved: "已解决",
};

export default function AlertCenterPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");

  const { alerts, loading, error, refresh, acknowledge } = useAlerts({
    status: statusFilter || undefined,
    severity: severityFilter || undefined,
  });

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">告警中心</h2>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-md"
        >
          <option value="">全部状态</option>
          <option value="active">活跃</option>
          <option value="acknowledged">已确认</option>
          <option value="suppressed">已抑制</option>
          <option value="resolved">已解决</option>
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-md"
        >
          <option value="">全部级别</option>
          <option value="critical">严重</option>
          <option value="high">高</option>
          <option value="warning">警告</option>
          <option value="info">信息</option>
        </select>
      </div>

      <StateWrapper
        loading={loading}
        error={error}
        empty={alerts.length === 0}
        emptyMessage="暂无告警"
        onRetry={refresh}
      >
        <div className="space-y-2">
          {alerts.map((alert) => (
            <AlertCard
              key={alert.alert_id}
              alert={alert}
              onAck={() => acknowledge(alert.alert_id)}
            />
          ))}
        </div>
      </StateWrapper>
    </div>
  );
}

function AlertCard({ alert, onAck }: { alert: Alert; onAck: () => void }) {
  const borderColor = SEVERITY_COLORS[alert.severity] ?? "border-l-gray-300";

  return (
    <div
      className={`border border-gray-200 rounded-lg p-3 border-l-4 ${borderColor}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                alert.severity === "critical"
                  ? "bg-red-100 text-red-700"
                  : alert.severity === "high"
                  ? "bg-orange-100 text-orange-700"
                  : "bg-amber-100 text-amber-700"
              }`}
            >
              {alert.severity}
            </span>
            <span className="text-xs text-gray-400">
              {STATUS_LABELS[alert.status] ?? alert.status}
            </span>
          </div>
          <p className="text-sm text-gray-900 mt-1">{alert.message}</p>
          <p className="text-xs text-gray-400 font-mono mt-0.5">
            {alert.txn_id} &middot;{" "}
            {new Date(alert.triggered_at).toLocaleString("zh-CN")}
          </p>
        </div>
        {alert.status === "active" && (
          <button
            onClick={onAck}
            className="text-xs px-2 py-1 border border-gray-200 rounded hover:bg-gray-50"
          >
            确认
          </button>
        )}
      </div>
    </div>
  );
}
