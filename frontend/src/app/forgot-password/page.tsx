"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, forgotPassword } from "@/lib/api";
import { Card } from "@/components/Card";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong");
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
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Reset password</h2>
        {sent ? (
          <>
            <p className="text-sm text-status-good">
              If that email is registered, a reset code has been sent to it.
            </p>
            <Link
              href={`/reset-password?email=${encodeURIComponent(email)}`}
              className="mt-4 inline-block text-sm font-medium text-series-1 hover:underline"
            >
              I have a code
            </Link>
          </>
        ) : (
          <>
            {error && <p className="mb-3 text-sm text-status-critical">{error}</p>}
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                placeholder="Email"
                required
                className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              />
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
              >
                Send reset code
              </button>
            </form>
          </>
        )}
        <p className="mt-4 text-center text-sm text-text-secondary">
          <button
            onClick={() => router.push("/login")}
            className="font-medium text-series-1 hover:underline"
          >
            Back to log in
          </button>
        </p>
      </Card>
    </div>
  );
}
