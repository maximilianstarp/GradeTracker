"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  ApiError,
  createStudiengang,
  deleteStudiengang,
  listStudiengaenge,
  updateStudiengang,
} from "@/lib/api";
import { Card } from "@/components/Card";
import { useConfirm } from "@/components/ConfirmDialog";
import type { Studiengang } from "@/lib/types";

export default function StudiengaengePage() {
  const confirm = useConfirm();
  const [studiengaenge, setStudiengaenge] = useState<Studiengang[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");

  const load = () =>
    listStudiengaenge()
      .then(setStudiengaenge)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createStudiengang(name.trim());
      setName("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create");
    }
  }

  async function handleRename(id: number) {
    try {
      await updateStudiengang(id, editingName.trim());
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to rename");
    }
  }

  async function handleDelete(id: number) {
    const ok = await confirm({
      title: "Delete program",
      message: "Assigned modules move to \"Other\". This action cannot be undone.",
      confirmLabel: "Delete",
      danger: true,
    });
    if (!ok) return;
    try {
      await deleteStudiengang(id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-text-primary">Programs</h1>
      </div>

      {error && (
        <Card className="border-status-critical/30 bg-status-critical/5 text-sm text-status-critical">
          {error}
        </Card>
      )}

      <Card>
        <form onSubmit={handleCreate} className="flex gap-2">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New program, e.g. Mathematics"
            required
            className="flex-1 rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
          />
          <button
            type="submit"
            className="rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Add
          </button>
        </form>
      </Card>

      {loading ? (
        <p className="text-text-secondary">Loading…</p>
      ) : studiengaenge.length === 0 ? (
        <p className="text-text-muted">No programs yet.</p>
      ) : (
        <div className="space-y-2">
          {studiengaenge.map((sg) => (
            <Card key={sg.id} className="flex items-center justify-between py-3">
              {editingId === sg.id ? (
                <div className="flex flex-1 gap-2">
                  <input
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    className="flex-1 rounded-lg border border-border bg-surface-raised px-3 py-1.5 text-sm outline-none focus:border-series-1"
                    autoFocus
                  />
                  <button
                    onClick={() => handleRename(sg.id)}
                    className="rounded-lg bg-series-1 px-3 py-1.5 text-sm font-medium text-white"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="rounded-lg px-3 py-1.5 text-sm text-text-secondary hover:bg-text-muted/10"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <>
                  <span className="font-medium text-text-primary">{sg.name}</span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => {
                        setEditingId(sg.id);
                        setEditingName(sg.name);
                      }}
                      className="rounded-lg px-3 py-1.5 text-sm text-text-secondary hover:bg-text-muted/10"
                    >
                      Rename
                    </button>
                    <button
                      onClick={() => handleDelete(sg.id)}
                      className="rounded-lg px-3 py-1.5 text-sm text-status-critical hover:bg-status-critical/10"
                    >
                      Delete
                    </button>
                  </div>
                </>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
