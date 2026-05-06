import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { fetchJSON } from "../lib/api";
import type { WorkflowStage, WorkflowTxnRef, WorkflowAgentRef } from "../lib/types";
import { getRoleLabel, getStateInfo } from "../lib/states";
import StateWrapper from "../components/StateWrapper";

export default function WorkflowPage() {
  const [stages, setStages] = useState<WorkflowStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJSON<{ stages: WorkflowStage[] }>(
        "/api/workflow/stages"
      );
      setStages(data.stages);
      // Auto-select first active stage
      if (!selectedStage) {
        const active = data.stages.find((s) => s.is_active);
        if (active) setSelectedStage(active.id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [selectedStage]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const selected = stages.find((s) => s.id === selectedStage);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">治理工作流</h2>

      <StateWrapper
        loading={loading}
        error={error}
        empty={stages.length === 0}
        emptyMessage="暂无工作流数据"
        onRetry={fetchData}
      >
        {/* Workflow pipeline */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center gap-1 overflow-x-auto">
            {stages.map((stage, i) => {
              const isActive = stage.is_active;
              const isSelected = stage.id === selectedStage;
              const hasAgents = stage.active_agents.length > 0;

              return (
                <div key={stage.id} className="flex items-center">
                  <button
                    onClick={() => setSelectedStage(stage.id)}
                    className={`flex flex-col items-center px-3 py-2.5 rounded-lg text-xs transition-all min-w-[90px] ${
                      isSelected
                        ? "bg-blue-50 border-2 border-blue-300 shadow-sm"
                        : isActive
                          ? "bg-blue-50/50 border border-blue-200"
                          : "bg-gray-50 border border-gray-200 hover:bg-gray-100"
                    }`}
                  >
                    <span
                      className={`font-medium ${
                        isSelected
                          ? "text-blue-800"
                          : isActive
                            ? "text-blue-700"
                            : "text-gray-500"
                      }`}
                    >
                      {stage.label}
                    </span>
                    <span className="text-[10px] text-gray-400 mt-0.5">
                      {getRoleLabel(stage.agent_role)}
                    </span>
                    {hasAgents && (
                      <div className="flex items-center gap-1 mt-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                        <span className="text-[10px] text-blue-600">
                          {stage.active_agents.length}个Agent
                        </span>
                      </div>
                    )}
                    {stage.active_transactions.length > 0 && (
                      <span className="text-[10px] text-gray-400 mt-0.5">
                        {stage.active_transactions.length}个任务
                      </span>
                    )}
                  </button>
                  {i < stages.length - 1 && (
                    <div
                      className={`w-3 h-px ${
                        stages[i + 1]?.is_active || isActive
                          ? "bg-blue-300"
                          : "bg-gray-200"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Stage detail panel */}
        {selected && <StageDetail stage={selected} navigate={navigate} />}
      </StateWrapper>
    </div>
  );
}

/* ── Stage Detail ─────────────────────────── */

function StageDetail({
  stage,
  navigate,
}: {
  stage: WorkflowStage;
  navigate: (path: string) => void;
}) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Left: Active agents + transactions */}
      <div className="col-span-2 space-y-4">
        {/* Active agents */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-1">
            当前阶段: {stage.label}
          </h3>
          <p className="text-xs text-gray-400 mb-4">{stage.description}</p>

          {stage.active_agents.length > 0 ? (
            <div className="space-y-2">
              {stage.active_agents.map((agent) => (
                <AgentActivityCard
                  key={agent.role}
                  agent={agent}
                  onClick={() => navigate(`/agents/${agent.role}`)}
                />
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-400 text-center py-4 bg-gray-50 rounded-lg">
              当前无活跃 Agent
            </div>
          )}
        </div>

        {/* Active transactions */}
        {stage.active_transactions.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              进行中的任务 ({stage.active_transactions.length})
            </h4>
            <div className="space-y-2">
              {stage.active_transactions.map((txn) => (
                <TxnRefCard
                  key={txn.txn_id}
                  txn={txn}
                  onClick={() => navigate(`/tasks/${txn.txn_id}`)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Completed transactions */}
        {stage.completed_transactions.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h4 className="text-sm font-medium text-gray-700 mb-3">
              已完成的任务 ({stage.completed_transactions.length})
            </h4>
            <div className="space-y-1.5">
              {stage.completed_transactions.map((txn) => (
                <TxnRefCard
                  key={txn.txn_id}
                  txn={txn}
                  compact
                  onClick={() => navigate(`/tasks/${txn.txn_id}`)}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right: Stage info */}
      <div className="space-y-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">阶段信息</h4>
          <div className="space-y-2.5 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">负责角色</span>
              <span className="text-gray-700">
                {getRoleLabel(stage.agent_role)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">活跃 Agent</span>
              <span className="text-gray-700">
                {stage.active_agents.length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">进行中任务</span>
              <span className="text-gray-700">
                {stage.active_transactions.length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">已完成任务</span>
              <span className="text-gray-700">
                {stage.completed_transactions.length}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">说明</h4>
          <p className="text-sm text-gray-600">{stage.description}</p>
        </div>
      </div>
    </div>
  );
}

/* ── Agent Activity Card ──────────────────── */

function AgentActivityCard({
  agent,
  onClick,
}: {
  agent: WorkflowAgentRef;
  onClick: () => void;
}) {
  const isActive = agent.lifecycle === "execute" || agent.lifecycle === "activated";

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-3 p-3 bg-blue-50/50 border border-blue-100 rounded-lg cursor-pointer hover:bg-blue-50 transition-colors"
    >
      <span className={`w-2.5 h-2.5 rounded-full ${isActive ? "bg-blue-500 animate-pulse" : "bg-gray-300"}`} />
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-800">
          {getRoleLabel(agent.role)}
        </div>
        <div className="text-xs text-gray-400">
          {isActive ? "执行中" : agent.lifecycle}
        </div>
      </div>
      {agent.active_contract && (
        <div className="text-[10px] text-gray-400 font-mono max-w-[120px] truncate">
          {agent.active_contract}
        </div>
      )}
    </div>
  );
}

/* ── Txn Reference Card ───────────────────── */

function TxnRefCard({
  txn,
  compact,
  onClick,
}: {
  txn: WorkflowTxnRef;
  compact?: boolean;
  onClick: () => void;
}) {
  const info = getStateInfo(txn.state);

  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-3 px-3 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
        compact ? "py-2" : "py-3"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full shrink-0 ${info.color.dot}`}
      />
      <div className="flex-1 min-w-0">
        <p className={`text-gray-800 truncate ${compact ? "text-xs" : "text-sm"}`}>
          {txn.goal}
        </p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[10px] text-gray-400 font-mono">
            {txn.txn_id}
          </span>
          {txn.sub_task_count > 0 && (
            <span className="text-[10px] text-gray-400">
              {txn.sub_task_count}个子任务
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
