"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError, createModul, listModule, listStudiengaenge } from "@/lib/api";
import { Card } from "@/components/Card";
import { GradeBadge } from "@/components/GradeBadge";
import { formatCredits } from "@/lib/format";
import type { Modul, Studiengang } from "@/lib/types";

const SONSTIGES = "sonstiges";
const ALLE = "alle";

export default function ModulePage() {
  const [studiengaenge, setStudiengaenge] = useState<Studiengang[]>([]);
  const [module, setModule] = useState<Modul[]>([]);
  const [filter, setFilter] = useState<string>(ALLE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [credits, setCredits] = useState("");
  const [studiengangId, setStudiengangId] = useState<string>(SONSTIGES);

  const load = () =>
    Promise.all([listStudiengaenge(), listModule()])
      .then(([sgs, mods]) => {
        setStudiengaenge(sgs);
        setModule(mods);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Fehler beim Laden"))
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    if (filter === ALLE) return module;
    if (filter === SONSTIGES) return module.filter((m) => m.studiengang_id === null);
    return module.filter((m) => m.studiengang_id === Number(filter));
  }, [module, filter]);

  function studiengangName(id: number | null) {
    if (id === null) return "Sonstiges";
    return studiengaenge.find((s) => s.id === id)?.name ?? "–";
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createModul({
        name: name.trim(),
        credits: Number(credits),
        studiengang_id: studiengangId === SONSTIGES ? null : Number(studiengangId),
      });
      setName("");
      setCredits("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Fehler beim Anlegen");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Module</h1>
        <p className="mt-1 text-text-secondary">
          Alle Module über deine Studiengänge hinweg – inklusive Noten und Klausurzulassung.
        </p>
      </div>

      {error && (
        <Card className="border-status-critical/30 bg-status-critical/5 text-sm text-status-critical">
          {error}
        </Card>
      )}

      <Card>
        <h2 className="mb-3 font-semibold text-text-primary">Neues Modul</h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 sm:grid-cols-[2fr_1fr_1.5fr_auto]">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name, z. B. Analysis I"
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
            <option value={SONSTIGES}>Sonstiges</option>
            {studiengaenge.map((sg) => (
              <option key={sg.id} value={sg.id}>
                {sg.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            className="rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Anlegen
          </button>
        </form>
      </Card>

      <div className="flex flex-wrap gap-2">
        <FilterChip active={filter === ALLE} onClick={() => setFilter(ALLE)} label="Alle" />
        {studiengaenge.map((sg) => (
          <FilterChip
            key={sg.id}
            active={filter === String(sg.id)}
            onClick={() => setFilter(String(sg.id))}
            label={sg.name}
          />
        ))}
        <FilterChip active={filter === SONSTIGES} onClick={() => setFilter(SONSTIGES)} label="Sonstiges" />
      </div>

      {loading ? (
        <p className="text-text-secondary">Lade…</p>
      ) : filtered.length === 0 ? (
        <p className="text-text-muted">Keine Module in dieser Ansicht.</p>
      ) : (
        <div className="space-y-2">
          {filtered.map((m) => (
            <Link key={m.id} href={`/module/${m.id}`}>
              <Card className="flex items-center justify-between transition-colors hover:border-series-1/40">
                <div>
                  <div className="font-medium text-text-primary">{m.name}</div>
                  <div className="mt-0.5 text-sm text-text-muted">
                    {studiengangName(m.studiengang_id)} · {formatCredits(m.credits)}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {!m.zulassung && (
                    <span className="text-sm text-status-critical" title="Klausurzulassung offen">
                      ⚠ Zulassung offen
                    </span>
                  )}
                  <GradeBadge grade={m.final_grade} />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-sm transition-colors ${
        active
          ? "border-series-1 bg-series-1/10 text-series-1"
          : "border-border text-text-secondary hover:bg-text-muted/10"
      }`}
    >
      {label}
    </button>
  );
}
