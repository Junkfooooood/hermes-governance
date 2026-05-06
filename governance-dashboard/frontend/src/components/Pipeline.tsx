import type { PipelineStage } from "../lib/types";

const DEFAULT_STAGES: PipelineStage[] = [
  { id: "interview", label: "Deep Interview", agent: "zhongshu" },
  { id: "plan", label: "规划", agent: "zhongshu" },
  { id: "review_spec", label: "Spec 审核", agent: "menxia" },
  { id: "review_quality", label: "质量审核", agent: "menxia" },
  { id: "decompose", label: "任务分解", agent: "shangshu" },
  { id: "dispatch", label: "派发", agent: "shangshu" },
  { id: "execute", label: "执行", agent: "六部" },
  { id: "verify", label: "验证", agent: "xingbu" },
  { id: "integrate", label: "整合", agent: "shangshu" },
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

interface PipelineProps {
  currentState: string;
  stages?: PipelineStage[];
  className?: string;
}

export default function Pipeline({
  currentState,
  stages = DEFAULT_STAGES,
  className = "",
}: PipelineProps) {
  const activeStage = STATE_TO_STAGE[currentState] ?? "";
  const isTerminal = ["complete", "rejected", "error"].includes(currentState);
  const activeIndex = stages.findIndex((s) => s.id === activeStage);

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {stages.map((stage, i) => {
        const isActive = !isTerminal && i === activeIndex;
        const isPast = isTerminal || i < activeIndex;
        const isError = currentState === "error" && i === activeIndex;

        return (
          <div key={stage.id} className="flex items-center">
            <div
              className={`flex flex-col items-center px-2 py-1 rounded-md text-xs transition-all ${
                isActive
                  ? "bg-blue-50 border border-blue-200 animate-pulse"
                  : isPast
                  ? "bg-green-50 border border-green-200"
                  : isError
                  ? "bg-red-50 border border-red-200"
                  : "bg-gray-50 border border-gray-200"
              }`}
            >
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
              <span className="text-[10px] text-gray-400">{stage.agent}</span>
            </div>
            {i < stages.length - 1 && (
              <div
                className={`w-4 h-px ${
                  isPast ? "bg-green-300" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
