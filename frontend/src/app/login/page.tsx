"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { Card } from "@/components/Card";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.replace("/");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Anmeldung fehlgeschlagen");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-center text-2xl font-semibold text-text-primary">
        🎓 Grade Tracker
      </h1>
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Anmelden</h2>
        {error && <p className="mb-3 text-sm text-status-critical">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            placeholder="E-Mail"
            required
            className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
          />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="Passwort"
            required
            className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
          />
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            Anmelden
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-text-secondary">
          Noch kein Konto?{" "}
          <Link href="/signup" className="font-medium text-series-1 hover:underline">
            Registrieren
          </Link>
        </p>
      </Card>
    </div>
  );
}
