"use client";

import { useState } from "react";
import { ApiError, deleteGrade, upsertGrade } from "@/lib/api";
import type { GradeAttempt, GradeKind, Modul } from "@/lib/types";

const SLOTS = [1, 2, 3];

export function GradeSlots({
  modulId,
  attempts,
  onModulUpdate,
}: {
  modulId: number;
  attempts: GradeAttempt[];
  onModulUpdate: (modul: Modul) => void;
}) {
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="space-y-2">
      {error && <p className="text-sm text-status-critical">{error}</p>}
      {SLOTS.map((slot) => {
        const attempt = attempts.find((a) => a.slot === slot);
        return (
          <GradeSlotRow
            key={slot}
            slot={slot}
            modulId={modulId}
            attempt={attempt}
            onModulUpdate={onModulUpdate}
            onError={setError}
          />
        );
      })}
    </div>
  );
}

function GradeSlotRow({
  slot,
  modulId,
  attempt,
  onModulUpdate,
  onError,
}: {
  slot: number;
  modulId: number;
  attempt: GradeAttempt | undefined;
  onModulUpdate: (modul: Modul) => void;
  onError: (msg: string | null) => void;
}) {
  const [kind, setKind] = useState<GradeKind>(attempt?.kind ?? "numeric");
  const [value, setValue] = useState(attempt?.value?.toString() ?? "");

  async function handleSave() {
    onError(null);
    try {
      const modul = await upsertGrade(modulId, {
        slot,
        kind,
        ...(kind === "numeric" ? { value: Number(value) } : {}),
      });
      onModulUpdate(modul);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to save the grade");
    }
  }

  async function handleClear() {
    if (!attempt) return;
    onError(null);
    try {
      const modul = await deleteGrade(attempt.id);
      onModulUpdate(modul);
      setValue("");
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Failed to delete");
    }
  }

  return (
    <div className="flex items-center gap-2">
      <span className="w-16 shrink-0 text-sm text-text-muted">Attempt {slot}</span>
      <select
        value={kind}
        onChange={(e) => setKind(e.target.value as GradeKind)}
        className="rounded-lg border border-border bg-surface-raised px-2 py-1.5 text-sm outline-none focus:border-series-1"
      >
        <option value="numeric">Grade</option>
        <option value="pass">Passed</option>
        <option value="fail">Failed</option>
      </select>
      {kind === "numeric" && (
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          type="number"
          min="1"
          max="5"
          step="0.1"
          placeholder="e.g. 1.7"
          className="w-24 rounded-lg border border-border bg-surface-raised px-2 py-1.5 text-sm outline-none focus:border-series-1"
        />
      )}
      <button
        onClick={handleSave}
        className="rounded-lg bg-series-1 px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
      >
        Save
      </button>
      {attempt && (
        <button
          onClick={handleClear}
          className="rounded-lg px-2 py-1.5 text-sm text-text-muted hover:bg-text-muted/10"
        >
          Clear
        </button>
      )}
    </div>
  );
}
