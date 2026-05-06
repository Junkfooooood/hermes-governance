import { getStateInfo } from "../lib/states";

interface StatusBadgeProps {
  state: string;
  showDot?: boolean;
  showDescription?: boolean;
  className?: string;
}

export default function StatusBadge({
  state,
  showDot = false,
  showDescription = false,
  className = "",
}: StatusBadgeProps) {
  const info = getStateInfo(state);
  const isActive = info.category === "active";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md ${info.color.bg} ${info.color.text} ${className}`}
      title={`${info.label} (${state}) — ${info.description}`}
    >
      {showDot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${info.color.dot} ${isActive ? "animate-pulse" : ""}`}
        />
      )}
      <span>{info.shortLabel}</span>
      {showDescription && (
        <span className="text-[10px] opacity-70 ml-1">{info.description}</span>
      )}
    </span>
  );
}
