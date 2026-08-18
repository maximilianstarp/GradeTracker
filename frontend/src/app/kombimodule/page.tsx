"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  ApiError,
  createKombimodul,
  deleteKombimodul,
  listKombimodule,
  listModule,
  listStudiengaenge,
} from "@/lib/api";
import { Card } from "@/components/Card";
import { useConfirm } from "@/components/ConfirmDialog";
import { GradeBadge } from "@/components/GradeBadge";
import { formatCredits } from "@/lib/format";
import type { KombiModul, Modul, Studiengang } from "@/lib/types";

export default function KombimodulePage() {
  const confirm = useConfirm();
  const [kombimodule, setKombimodule] = useState<KombiModul[]>([]);
  const [studiengaenge, setStudiengaenge] = useState<Studiengang[]>([]);
  const [module, setModule] = useState<Modul[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [credits, setCredits] = useState("");
  const [studiengangId, setStudiengangId] = useState("");
  const [sourceIds, setSourceIds] = useState<number[]>([]);
  const [graded, setGraded] = useState(true);

  const load = () =>
    Promise.all([listKombimodule(), listStudiengaenge(), listModule()])
      .then(([k, sgs, mods]) => {
        setKombimodule(k);
        setStudiengaenge(sgs);
        setModule(mods);
        if (!studiengangId && sgs.length > 0) setStudiengangId(String(sgs[0].id));
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggleSource(id: number) {
    setSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (sourceIds.length < 1) {
      setError("Please select at least one source module");
      return;
    }
    try {
      await createKombimodul({
        name: name.trim(),
        credits: Number(credits),
        studiengang_id: Number(studiengangId),
        source_module_ids: sourceIds,
        graded,
      });
      setName("");
      setCredits("");
      setSourceIds([]);
      setGraded(true);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create");
    }
  }

  async function handleDelete(id: number) {
    const ok = await confirm({
      title: "Delete combined module",
      message: "The source modules stay intact, only this combination is deleted.",
      confirmLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    try {
      await deleteKombimodul(id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Combined Modules</h1>
      </div>

      {error && (
        <Card className="border-status-critical/30 bg-status-critical/5 text-sm text-status-critical">
          {error}
        </Card>
      )}

      {studiengaenge.length === 0 ? (
        <p className="text-text-muted">
          Create a program first – combined modules need a program.
        </p>
      ) : (
        <Card>
          <h2 className="mb-3 font-semibold text-text-primary">New Combined Module</h2>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Name, e.g. Math for Physicists"
                required
                className="rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              />
              <input
                value={credits}
                onChange={(e) => setCredits(e.target.value)}
                placeholder="Credits"
                type="number"
                min="0.5"
                step="0.5"
                required
                className="rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              />
              <select
                value={studiengangId}
                onChange={(e) => setStudiengangId(e.target.value)}
                className="rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              >
                {studiengaenge.map((sg) => (
                  <option key={sg.id} value={sg.id}>
                    {sg.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <p className="mb-2 text-sm text-text-secondary">
                Source modules – a single module is fine too (e.g. to re-credit it under
                different credits):
              </p>
              <div className="flex flex-wrap gap-2">
                {module.map((m) => (
                  <label
                    key={m.id}
                    className={`flex cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-sm ${
                      sourceIds.includes(m.id)
                        ? "border-series-1 bg-series-1/10 text-series-1"
                        : "border-border text-text-secondary hover:bg-text-muted/10"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={sourceIds.includes(m.id)}
                      onChange={() => toggleSource(m.id)}
                      className="hidden"
                    />
                    {m.name}
                  </label>
                ))}
              </div>
            </div>

            <label className="flex cursor-pointer items-start gap-2 text-sm text-text-secondary">
              <input
                type="checkbox"
                checked={graded}
                onChange={(e) => setGraded(e.target.checked)}
                className="mt-0.5"
              />
              <span>
                Graded (benotet) – averages the source modules&apos; grades. Uncheck for an
                ungraded (unbenotet) combined module: it counts as passed once every source
                module has passed, with no numeric grade of its own.
              </span>
            </label>

            <button
              type="submit"
              className="rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            >
              Add
            </button>
          </form>
        </Card>
      )}

      {loading ? (
        <p className="text-text-secondary">Loading…</p>
      ) : kombimodule.length === 0 ? (
        <p className="text-text-muted">No combined modules yet.</p>
      ) : (
        <div className="space-y-2">
          {kombimodule.map((k) => (
            <Card key={k.id} className="flex items-center justify-between">
              <div>
                <div className="font-medium text-text-primary">
                  {k.name}
                  {!k.graded && (
                    <span className="ml-2 rounded-full bg-text-muted/10 px-2 py-0.5 text-xs font-normal text-text-muted">
                      unbenotet
                    </span>
                  )}
                </div>
                <div className="mt-0.5 text-sm text-text-muted">
                  {studiengaenge.find((s) => s.id === k.studiengang_id)?.name} ·{" "}
                  {formatCredits(k.credits)} · from {k.source_module.map((m) => m.name).join(" + ")}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <GradeBadge grade={k.final_grade} />
                <button
                  onClick={() => handleDelete(k.id)}
                  className="rounded-lg px-3 py-1.5 text-sm text-status-critical hover:bg-status-critical/10"
                >
                  Delete
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
