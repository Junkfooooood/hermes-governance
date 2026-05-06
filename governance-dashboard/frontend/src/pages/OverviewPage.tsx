import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchJSON } from "../lib/api";
import type { OverviewStats, AgentState } from "../lib/types";
import StateWrapper from "../components/StateWrapper";
import MetricsCard from "../components/MetricsCard";
import StatusBadge from "../components/StatusBadge";
import AgentCard from "../components/AgentCard";

export default function OverviewPage() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJSON<OverviewStats>("/api/overview");
      setStats(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">总览</h2>

      <StateWrapper
        loading={loading}
        error={error}
        empty={!stats || stats.total_transactions === 0}
        emptyMessage="暂无事务数据，等待治理链执行..."
        onRetry={fetchData}
      >
        {stats && (
          <>
            {/* Metrics */}
            <div className="grid grid-cols-4 gap-4">
              <MetricsCard label="总任务" value={stats.total_transactions} />
              <MetricsCard label="进行中" value={stats.active_count} />
              <MetricsCard label="已完成" value={stats.completed_count} />
              <MetricsCard label="异常" value={stats.error_count} />
            </div>

            {/* Recent tasks */}
            {stats.recent_transactions.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h3 className="text-sm font-medium text-gray-700">最近任务</h3>
                </div>
                <div className="divide-y divide-gray-100">
                  {stats.recent_transactions.map((t) => (
                    <div
                      key={t.txn_id}
                      onClick={() => navigate(`/tasks/${t.txn_id}`)}
                      className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 truncate">{t.goal}</p>
                        <p className="text-xs text-gray-400 font-mono">{t.txn_id}</p>
                      </div>
                      <StatusBadge state={t.state} showDot />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Agent summary */}
            {stats.agent_summary.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">Agent 状态</h3>
                <div className="grid grid-cols-3 gap-3">
                  {stats.agent_summary.map((a: AgentState) => (
                    <AgentCard
                      key={a.role}
                      agent={a}
                      onClick={() => navigate(`/agents/${a.role}`)}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </StateWrapper>
    </div>
  );
}
