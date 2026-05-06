import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchJSON } from "../lib/api";
import type { Transaction } from "../lib/types";
import StateWrapper from "../components/StateWrapper";
import StatusBadge from "../components/StatusBadge";
import Timeline from "../components/Timeline";

export default function AuditReplayPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Transaction | null>(null);
  const [stateFilter, setStateFilter] = useState("");
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      if (stateFilter) qs.set("state", stateFilter);
      qs.set("limit", "50");
      const data = await fetchJSON<{ transactions: Transaction[] }>(
        `/api/audit/transactions?${qs}`
      );
      setTransactions(data.transactions);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [stateFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">审计回放</h2>

      <div className="flex items-center gap-3">
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-md"
        >
          <option value="">全部状态</option>
          <option value="complete">已完成</option>
          <option value="error">错误</option>
          <option value="rejected">已拒绝</option>
        </select>
      </div>

      <StateWrapper
        loading={loading}
        error={error}
        empty={transactions.length === 0}
        emptyMessage="暂无可审计的事务"
        onRetry={fetchData}
      >
        <div className="grid grid-cols-3 gap-4">
          {/* Transaction list */}
          <div className="col-span-1 bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-3 py-2 bg-gray-50 border-b border-gray-100">
              <p className="text-xs font-medium text-gray-500">事务列表</p>
            </div>
            <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
              {transactions.map((t) => (
                <div
                  key={t.txn_id}
                  onClick={() => setSelected(t)}
                  className={`px-3 py-2 cursor-pointer hover:bg-gray-50 ${
                    selected?.txn_id === t.txn_id ? "bg-blue-50" : ""
                  }`}
                >
                  <p className="text-sm text-gray-900 truncate">{t.goal}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-400 font-mono">
                      {t.txn_id}
                    </span>
                    <StatusBadge state={t.state} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Detail panel */}
          <div className="col-span-2">
            {selected ? (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">
                      {selected.goal}
                    </h3>
                    <p className="text-xs text-gray-400 font-mono">
                      {selected.txn_id}
                    </p>
                  </div>
                  <button
                    onClick={() => navigate(`/tasks/${selected.txn_id}`)}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    查看详情
                  </button>
                </div>
                <Timeline entries={selected.audit_trail} />
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <p className="text-sm text-gray-400">选择一个事务查看审计记录</p>
              </div>
            )}
          </div>
        </div>
      </StateWrapper>
    </div>
  );
}
