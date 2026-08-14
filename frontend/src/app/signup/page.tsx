"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { Card } from "@/components/Card";

export default function SignupPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(name, email, password);
      router.replace("/");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Registrierung fehlgeschlagen");
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
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Registrieren</h2>
        {error && <p className="mb-3 text-sm text-status-critical">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            required
            className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
          />
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
            placeholder="Passwort (mind. 8 Zeichen)"
            minLength={8}
            required
            className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
          />
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            Konto erstellen
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-text-secondary">
          Schon ein Konto?{" "}
          <Link href="/login" className="font-medium text-series-1 hover:underline">
            Anmelden
          </Link>
        </p>
      </Card>
    </div>
  );
}
