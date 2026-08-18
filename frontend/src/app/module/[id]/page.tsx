"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ApiError,
  deleteModul,
  getModul,
  listStudiengaenge,
  updateModul,
} from "@/lib/api";
import { Card } from "@/components/Card";
import { useConfirm } from "@/components/ConfirmDialog";
import { GradeBadge } from "@/components/GradeBadge";
import { GradeSlots } from "@/components/GradeSlots";
import { NotGradedBadge } from "@/components/NotGradedBadge";
import { SeriesEditor } from "@/components/SeriesEditor";
import { StudiengangMultiSelect } from "@/components/StudiengangMultiSelect";
import { formatCredits } from "@/lib/format";
import type { Modul, Studiengang } from "@/lib/types";

export default function ModulDetailPage(props: PageProps<"/module/[id]">) {
  const { id } = use(props.params);
  const modulId = Number(id);
  const router = useRouter();
  const confirm = useConfirm();

  const [modul, setModul] = useState<Modul | null>(null);
  const [studiengaenge, setStudiengaenge] = useState<Studiengang[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingHeader, setEditingHeader] = useState(false);
  const [name, setName] = useState("");
  const [credits, setCredits] = useState("");
  const [studiengangIds, setStudiengangIds] = useState<number[]>([]);
  const [graded, setGraded] = useState(true);

  useEffect(() => {
    Promise.all([getModul(modulId), listStudiengaenge()])
      .then(([m, sgs]) => {
        setModul(m);
        setStudiengaenge(sgs);
        setName(m.name);
        setCredits(String(m.credits));
        setStudiengangIds(m.studiengang_ids);
        setGraded(m.graded);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"));
  }, [modulId]);

  async function handleSaveHeader() {
    setError(null);
    try {
      const updated = await updateModul(modulId, {
        name: name.trim(),
        credits: Number(credits),
        studiengang_ids: studiengangIds,
        graded,
      });
      setModul(updated);
      setEditingHeader(false);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to save");
    }
  }

  async function handleDelete() {
    const ok = await confirm({
      title: "Delete module",
      message: `"${modul?.name}" will be permanently deleted along with all grades and submissions.`,
      confirmLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    try {
      await deleteModul(modulId);
      router.push("/module");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete");
    }
  }

  if (error && !modul) {
    return (
      <Card className="border-status-critical/30 bg-status-critical/5 text-status-critical">
        {error}
      </Card>
    );
  }

  if (!modul) {
    return <p className="text-text-secondary">Loading module…</p>;
  }

  return (
    <div className="space-y-6">
      <Link href="/module" className="text-sm text-text-secondary hover:underline">
        ← Back to modules
      </Link>

      {error && (
        <Card className="border-status-critical/30 bg-status-critical/5 text-sm text-status-critical">
          {error}
        </Card>
      )}

      <Card>
        {editingHeader ? (
          <div className="space-y-3">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-lg font-semibold outline-none focus:border-series-1"
            />
            <input
              value={credits}
              onChange={(e) => setCredits(e.target.value)}
              type="number"
              min="0.5"
              step="0.5"
              className="w-32 rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
            />
            <StudiengangMultiSelect
              studiengaenge={studiengaenge}
              selectedIds={studiengangIds}
              onChange={setStudiengangIds}
            />
            <label className="flex cursor-pointer items-center gap-2 text-sm text-text-secondary">
              <input
                type="checkbox"
                checked={graded}
                onChange={(e) => setGraded(e.target.checked)}
              />
              Graded
            </label>
            <div className="flex gap-2">
              <button
                onClick={handleSaveHeader}
                className="rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              >
                Save
              </button>
              <button
                onClick={() => setEditingHeader(false)}
                className="rounded-lg px-4 py-2 text-sm text-text-secondary hover:bg-text-muted/10"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-text-primary">
                {modul.name}
                {!modul.graded && <NotGradedBadge />}
              </h1>
              <p className="mt-1 text-text-secondary">
                {modul.studiengaenge.length > 0
                  ? modul.studiengaenge.map((s) => s.name).join(", ")
                  : "Other"}{" "}
                · {formatCredits(modul.credits)}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <GradeBadge grade={modul.final_grade} />
              <button
                onClick={() => setEditingHeader(true)}
                className="rounded-lg px-3 py-1.5 text-sm text-text-secondary hover:bg-text-muted/10"
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                className="rounded-lg px-3 py-1.5 text-sm text-status-critical hover:bg-status-critical/10"
              >
                Delete
              </button>
            </div>
          </div>
        )}

        {modul.series.length > 0 && (
          <div
            className={`mt-4 rounded-lg px-3 py-2 text-sm ${
              modul.zulassung
                ? "bg-status-good/10 text-status-good"
                : "bg-status-critical/10 text-status-critical"
            }`}
          >
            {modul.zulassung ? "✓ Exam admission reached" : "⚠ Exam admission not yet reached"}
          </div>
        )}
      </Card>

      <Card>
        <h2 className="mb-3 font-semibold text-text-primary">Grades</h2>
        <p className="mb-3 text-sm text-text-muted">
          {modul.graded
            ? "Up to three attempts – the best grade counts. Either a grade or \"passed\" / \"failed\"."
            : "This module is not graded – up to three attempts, either \"passed\" or \"failed\"."}
        </p>
        <GradeSlots
          modulId={modul.id}
          attempts={modul.grade_attempts}
          graded={modul.graded}
          onModulUpdate={setModul}
        />
      </Card>

      <Card>
        <h2 className="mb-3 font-semibold text-text-primary">Assignment Series &amp; Submissions</h2>
        <p className="mb-3 text-sm text-text-muted">
          Weekly submissions per series (e.g. problem set, programming exercise). Default exam
          admission threshold: 50%.
        </p>
        <SeriesEditor modulId={modul.id} series={modul.series} onModulUpdate={setModul} />
      </Card>
    </div>
  );
}
