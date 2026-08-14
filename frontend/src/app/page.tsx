"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getOverview } from "@/lib/api";
import { Card } from "@/components/Card";
import { CreditsChart, CreditsChartRow } from "@/components/CreditsChart";
import { StatTile } from "@/components/StatTile";
import { formatCredits, formatGradeValue } from "@/lib/format";
import type { Overview } from "@/lib/types";

export default function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getOverview()
      .then(setOverview)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to connect to the server"));
  }, []);

  if (error) {
    return (
      <Card className="border-status-critical/30 bg-status-critical/5 text-status-critical">
        {error}. Is the backend running? (`docker compose up`)
      </Card>
    );
  }

  if (!overview) {
    return <p className="text-text-secondary">Loading overview…</p>;
  }

  const rows: CreditsChartRow[] = [
    ...overview.studiengaenge.map((s) => ({
      key: `sg-${s.id}`,
      label: s.name,
      graded: s.graded_credits,
      ungradedPass: s.ungraded_pass_credits,
    })),
    {
      key: "sonstiges",
      label: overview.sonstiges.name,
      graded: overview.sonstiges.graded_credits,
      ungradedPass: overview.sonstiges.ungraded_pass_credits,
    },
  ].filter((r) => r.graded + r.ungradedPass > 0);

  const openZulassung = overview.overall.open_zulassung;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile
          label="Overall Average"
          value={overview.overall.average !== null ? formatGradeValue(overview.overall.average) : "–"}
          sublabel={`${formatCredits(overview.overall.graded_credits)} graded`}
        />
        <StatTile label="Total Credits" value={String(Math.round(overview.overall.total_credits * 10) / 10)} />
        <StatTile label="Open Exam Admissions" value={String(openZulassung.length)} />
      </div>

      {rows.length > 0 && (
        <Card>
          <h2 className="mb-4 text-lg font-semibold text-text-primary">Credits by Program</h2>
          <CreditsChart rows={rows} />
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {[...overview.studiengaenge, overview.sonstiges].map((s) => (
          <Card key={s.id ?? "sonstiges"}>
            <div className="flex items-start justify-between">
              <h3 className="font-semibold text-text-primary">{s.name}</h3>
              <span className="tabular-nums text-lg font-semibold text-text-primary">
                {s.average !== null ? formatGradeValue(s.average) : "–"}
              </span>
            </div>
            <p className="mt-1 text-sm text-text-muted">
              {formatCredits(s.total_credits)} · {s.module_count} module{s.module_count === 1 ? "" : "s"}
            </p>
            {s.open_zulassung.length > 0 && (
              <ul className="mt-3 space-y-1 border-t border-border pt-3 text-sm">
                {s.open_zulassung.map((m) => (
                  <li key={m.modul_id}>
                    <Link href={`/module/${m.modul_id}`} className="text-status-critical hover:underline">
                      ⚠ {m.modul_name} – exam admission open
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
