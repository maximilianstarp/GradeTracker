import { formatCredits } from "@/lib/format";

export interface CreditsChartRow {
  key: string;
  label: string;
  graded: number;
  ungradedPass: number;
}

export function CreditsChart({ rows }: { rows: CreditsChartRow[] }) {
  const max = Math.max(1, ...rows.map((r) => r.graded + r.ungradedPass));

  return (
    <div>
      <div className="mb-4 flex items-center gap-4 text-sm text-text-secondary">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-series-1" /> Benotet
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-series-3" /> Bestanden (unbenotet)
        </span>
      </div>
      <div className="space-y-3">
        {rows.map((row) => {
          const total = row.graded + row.ungradedPass;
          const gradedPct = (row.graded / max) * 100;
          const passPct = (row.ungradedPass / max) * 100;
          return (
            <div key={row.key}>
              <div className="mb-1 flex items-baseline justify-between text-sm">
                <span className="text-text-primary">{row.label}</span>
                <span className="tabular-nums text-text-muted">{formatCredits(total)}</span>
              </div>
              <div className="flex h-2.5 gap-[2px] overflow-hidden rounded-full bg-gridline">
                {row.graded > 0 && (
                  <div
                    className="h-full rounded-full bg-series-1"
                    style={{ width: `${gradedPct}%` }}
                  />
                )}
                {row.ungradedPass > 0 && (
                  <div
                    className="h-full rounded-full bg-series-3"
                    style={{ width: `${passPct}%` }}
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
