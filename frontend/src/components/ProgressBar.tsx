import { formatPercent } from "@/lib/format";

export function ProgressBar({
  percent,
  thresholdPercent,
  passed,
  label,
}: {
  percent: number | null;
  thresholdPercent: number;
  passed: boolean;
  label?: string;
}) {
  const clamped = percent === null ? 0 : Math.min(100, Math.max(0, percent));
  const barColor = passed ? "bg-status-good" : "bg-status-critical";

  return (
    <div>
      {label && (
        <div className="mb-1.5 flex items-baseline justify-between text-sm">
          <span className="text-text-secondary">{label}</span>
          <span className="tabular-nums font-medium text-text-primary">
            {formatPercent(percent)}
          </span>
        </div>
      )}
      <div className="relative h-2 w-full rounded-full bg-gridline">
        <div
          className={`h-2 rounded-full transition-[width] ${barColor}`}
          style={{ width: `${clamped}%` }}
        />
        <div
          className="absolute top-1/2 h-3.5 w-px -translate-y-1/2 bg-text-muted"
          style={{ left: `${thresholdPercent}%` }}
          title={`Threshold: ${thresholdPercent}%`}
        />
      </div>
    </div>
  );
}
