interface MetricsCardProps {
  label: string;
  value: number | string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  className?: string;
}

export default function MetricsCard({
  label,
  value,
  trend,
  trendValue,
  className = "",
}: MetricsCardProps) {
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        {trend && trendValue && (
          <span
            className={`text-xs font-medium ${
              trend === "up"
                ? "text-green-600"
                : trend === "down"
                ? "text-red-600"
                : "text-gray-400"
            }`}
          >
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue}
          </span>
        )}
      </div>
    </div>
  );
}
