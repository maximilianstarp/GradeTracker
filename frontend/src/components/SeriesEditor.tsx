"use client";

import { FormEvent, useState } from "react";
import {
  ApiError,
  createSeries,
  createSubmission,
  deleteSeries,
  deleteSubmission,
} from "@/lib/api";
import { ProgressBar } from "@/components/ProgressBar";
import { useConfirm } from "@/components/ConfirmDialog";
import { formatPercent } from "@/lib/format";
import type { Modul, SubmissionSeries } from "@/lib/types";

export function SeriesEditor({
  modulId,
  series,
  onModulUpdate,
}: {
  modulId: number;
  series: SubmissionSeries[];
  onModulUpdate: (modul: Modul) => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [showNewSeries, setShowNewSeries] = useState(false);
  const [seriesName, setSeriesName] = useState("");
  const [threshold, setThreshold] = useState("50");
  const [totalWeeks, setTotalWeeks] = useState("");

  async function handleCreateSeries(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const modul = await createSeries(modulId, {
        name: seriesName.trim(),
        threshold_percent: Number(threshold),
        ...(totalWeeks ? { total_weeks: Number(totalWeeks) } : {}),
      });
      onModulUpdate(modul);
      setSeriesName("");
      setThreshold("50");
      setTotalWeeks("");
      setShowNewSeries(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Fehler beim Anlegen der Übungsserie");
    }
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-status-critical">{error}</p>}

      {series.map((s) => (
        <SeriesCard key={s.id} series={s} onModulUpdate={onModulUpdate} onError={setError} />
      ))}

      {showNewSeries ? (
        <form
          onSubmit={handleCreateSeries}
          className="grid grid-cols-1 gap-2 rounded-lg border border-dashed border-border p-3 sm:grid-cols-[2fr_1fr_1fr_auto_auto]"
        >
          <input
            value={seriesName}
            onChange={(e) => setSeriesName(e.target.value)}
            placeholder="Name, z. B. Rechenblatt"
            required
            className="rounded-lg border border-border bg-surface-raised px-3 py-1.5 text-sm outline-none focus:border-series-1"
          />
          <input
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            type="number"
            min="0"
            max="100"
            placeholder="Schwelle %"
            className="rounded-lg border border-border bg-surface-raised px-3 py-1.5 text-sm outline-none focus:border-series-1"
          />
          <input
            value={totalWeeks}
            onChange={(e) => setTotalWeeks(e.target.value)}
            type="number"
            min="1"
            placeholder="Wochen (optional)"
            className="rounded-lg border border-border bg-surface-raised px-3 py-1.5 text-sm outline-none focus:border-series-1"
          />
          <button
            type="submit"
            className="rounded-lg bg-series-1 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
          >
            Anlegen
          </button>
          <button
            type="button"
            onClick={() => setShowNewSeries(false)}
            className="rounded-lg px-3 py-1.5 text-sm text-text-secondary hover:bg-text-muted/10"
          >
            Abbrechen
          </button>
        </form>
      ) : (
        <button
          onClick={() => setShowNewSeries(true)}
          className="text-sm font-medium text-series-1 hover:underline"
        >
          + Übungsserie hinzufügen
        </button>
      )}
    </div>
  );
}

function SeriesCard({
  series,
  onModulUpdate,
  onError,
}: {
  series: SubmissionSeries;
  onModulUpdate: (modul: Modul) => void;
  onError: (msg: string | null) => void;
}) {
  const confirm = useConfirm();
  const [week, setWeek] = useState("");
  const [achieved, setAchieved] = useState("");
  const [max, setMax] = useState("");

  async function handleAddSubmission(e: FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      const modul = await createSubmission(series.id, {
        week_number: Number(week),
        points_achieved: Number(achieved),
        points_max: Number(max),
      });
      onModulUpdate(modul);
      setWeek((Number(week) + 1).toString());
      setAchieved("");
      setMax(max); // keep max points prefilled for the next week
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Fehler beim Speichern der Abgabe");
    }
  }

  async function handleDeleteSubmission(id: number) {
    onError(null);
    try {
      const modul = await deleteSubmission(id);
      onModulUpdate(modul);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Fehler beim Löschen");
    }
  }

  async function handleDeleteSeries() {
    const ok = await confirm({
      title: "Übungsserie löschen",
      message: `„${series.name}“ wird inklusive aller erfassten Abgaben gelöscht.`,
      confirmLabel: "Löschen",
      danger: true,
    });
    if (!ok) return;
    onError(null);
    try {
      const modul = await deleteSeries(series.id);
      onModulUpdate(modul);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Fehler beim Löschen");
    }
  }

  return (
    <div className="rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-text-primary">{series.name}</h4>
        <button
          onClick={handleDeleteSeries}
          className="text-xs text-text-muted hover:text-status-critical"
        >
          Serie löschen
        </button>
      </div>
      <div className="mt-2">
        <ProgressBar
          percent={series.progress.percent}
          thresholdPercent={series.threshold_percent}
          passed={series.progress.passed}
        />
        <p className="mt-1.5 text-xs text-text-muted">
          {series.progress.points_achieved} / {series.progress.points_max} Punkte ·{" "}
          {formatPercent(series.progress.percent)}
          {!series.progress.passed && series.progress.points_max > 0 && (
            <> · noch {series.progress.points_needed} Punkte bis {series.threshold_percent}%</>
          )}
        </p>
      </div>

      {series.submissions.length > 0 && (
        <table className="mt-3 w-full text-sm">
          <thead>
            <tr className="text-left text-text-muted">
              <th className="pb-1 font-normal">Woche</th>
              <th className="pb-1 font-normal">Erreicht</th>
              <th className="pb-1 font-normal">Maximal</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {series.submissions.map((sub) => (
              <tr key={sub.id} className="border-t border-border">
                <td className="py-1 tabular-nums">{sub.week_number}</td>
                <td className="py-1 tabular-nums">{sub.points_achieved}</td>
                <td className="py-1 tabular-nums">{sub.points_max}</td>
                <td className="py-1 text-right">
                  <button
                    onClick={() => handleDeleteSubmission(sub.id)}
                    className="text-xs text-text-muted hover:text-status-critical"
                  >
                    Entfernen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form onSubmit={handleAddSubmission} className="mt-3 flex items-end gap-2">
        <Field label="Woche">
          <input
            value={week}
            onChange={(e) => setWeek(e.target.value)}
            type="number"
            min="1"
            required
            className="w-16 rounded-lg border border-border bg-surface-raised px-2 py-1.5 text-sm outline-none focus:border-series-1"
          />
        </Field>
        <Field label="Erreicht">
          <input
            value={achieved}
            onChange={(e) => setAchieved(e.target.value)}
            type="number"
            min="0"
            step="0.5"
            required
            className="w-20 rounded-lg border border-border bg-surface-raised px-2 py-1.5 text-sm outline-none focus:border-series-1"
          />
        </Field>
        <Field label="Maximal">
          <input
            value={max}
            onChange={(e) => setMax(e.target.value)}
            type="number"
            min="0.5"
            step="0.5"
            required
            className="w-20 rounded-lg border border-border bg-surface-raised px-2 py-1.5 text-sm outline-none focus:border-series-1"
          />
        </Field>
        <button
          type="submit"
          className="rounded-lg bg-series-1 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
        >
          Hinzufügen
        </button>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-xs text-text-muted">
      <span className="mb-1 block">{label}</span>
      {children}
    </label>
  );
}
