import { useState } from "react";
import type { AuditEntry } from "../lib/types";

interface TimelineProps {
  entries: AuditEntry[];
  className?: string;
}

const ACTION_COLORS: Record<string, string> = {
  complete: "bg-green-500",
  approved: "bg-green-500",
  rejected: "bg-red-500",
  revise: "bg-amber-500",
  error: "bg-red-500",
  retry: "bg-amber-500",
  decomposed: "bg-blue-500",
  verify_passed: "bg-green-500",
  verify_failed: "bg-red-500",
};

export default function Timeline({ entries, className = "" }: TimelineProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (i: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  };

  if (!entries.length) {
    return (
      <p className="text-sm text-gray-400">暂无审计记录</p>
    );
  }

  return (
    <div className={`space-y-0 ${className}`}>
      {entries.map((entry, i) => {
        const dotColor = ACTION_COLORS[entry.action] ?? "bg-gray-400";
        const isExpanded = expanded.has(i);
        const extraKeys = Object.keys(entry).filter(
          (k) => k !== "step" && k !== "action"
        );

        return (
          <div key={i} className="flex gap-3">
            {/* Timeline line + dot */}
            <div className="flex flex-col items-center">
              <div className={`w-2.5 h-2.5 rounded-full mt-1.5 ${dotColor}`} />
              {i < entries.length - 1 && (
                <div className="w-px flex-1 bg-gray-200" />
              )}
            </div>

            {/* Content */}
            <div
              className="pb-4 flex-1 cursor-pointer"
              onClick={() => toggle(i)}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-500">
                  {entry.step}
                </span>
                <span
                  className={`text-xs px-1.5 py-0.5 rounded ${
                    entry.action === "error" || entry.action === "rejected"
                      ? "bg-red-50 text-red-700"
                      : entry.action === "approved" || entry.action === "complete"
                      ? "bg-green-50 text-green-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {entry.action}
                </span>
              </div>
              {isExpanded && extraKeys.length > 0 && (
                <pre className="mt-1 text-xs text-gray-500 bg-gray-50 rounded p-2 overflow-x-auto font-mono">
                  {JSON.stringify(
                    Object.fromEntries(extraKeys.map((k) => [k, entry[k]])),
                    null,
                    2
                  )}
                </pre>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
