import type { AgentState } from "../lib/types";
import { getAgentLifecycle, getRoleLabel } from "../lib/states";

const TIER_COLORS: Record<string, string> = {
  ministry: "bg-blue-50 border-blue-200",
  department: "bg-emerald-50 border-emerald-200",
};

interface AgentCardProps {
  agent: AgentState;
  onClick?: () => void;
}

export default function AgentCard({ agent, onClick }: AgentCardProps) {
  const tierColor = TIER_COLORS[agent.tier] ?? "bg-gray-50 border-gray-200";
  const lc = getAgentLifecycle(agent.lifecycle);
  const label = getRoleLabel(agent.role);
  const isActive =
    agent.lifecycle === "execute" || agent.lifecycle === "activated";

  return (
    <div
      onClick={onClick}
      className={`border rounded-lg p-3 cursor-pointer hover:shadow-sm transition-shadow ${tierColor}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-900">{label}</p>
          <p className="text-xs text-gray-400">{agent.role}</p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 text-xs px-1.5 py-0.5 rounded ${
            isActive
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-500"
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
      <div className="mt-2 flex gap-4 text-xs text-gray-500">
        <span>任务: {agent.total_tasks_completed}</span>
        <span>Token: {agent.total_tokens_consumed.toLocaleString()}</span>
        <span>信任: {(agent.trust_score * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}
