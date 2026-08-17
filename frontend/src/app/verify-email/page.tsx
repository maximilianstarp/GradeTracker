"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ApiError, resendCode, verifyEmail, verifyEmailChange } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { Card } from "@/components/Card";

export default function VerifyEmailPage() {
  const { user, setUser } = useAuth();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);

  if (!user) return null;

  // A pending email change takes priority - that's the address whose code
  // was most recently sent (see resend-code on the backend, which follows
  // whichever purpose is currently pending).
  const target = user.pending_email ?? user.email;
  const alreadyVerified = !user.pending_email && user.email_verified;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const updated = user!.pending_email ? await verifyEmailChange(code) : await verifyEmail(code);
      setUser(updated);
      setCode("");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Verification failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResend() {
    setError(null);
    setResendMessage(null);
    setResending(true);
    try {
      await resendCode();
      setResendMessage("A new code has been sent.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to resend code");
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-center text-2xl font-semibold text-text-primary">
        🎓 Grade Tracker
      </h1>
      <Card>
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Verify your email</h2>

        {alreadyVerified ? (
          <>
            <p className="text-sm text-status-good">
              Your email ({user.email}) is verified. Nothing else to do here.
            </p>
            <Link
              href="/account"
              className="mt-4 inline-block text-sm font-medium text-series-1 hover:underline"
            >
              Back to account
            </Link>
          </>
        ) : (
          <>
            <p className="mb-4 text-sm text-text-secondary">
              We sent a 6-digit code to <span className="font-medium">{target}</span>. Enter it
              below to confirm this address.
            </p>
            {error && <p className="mb-3 text-sm text-status-critical">{error}</p>}
            {resendMessage && <p className="mb-3 text-sm text-status-good">{resendMessage}</p>}
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                placeholder="123456"
                minLength={6}
                maxLength={6}
                required
                className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-center text-lg tracking-[0.3em] outline-none focus:border-series-1"
              />
              <button
                type="submit"
                disabled={submitting || code.length !== 6}
                className="w-full rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
              >
                Confirm
              </button>
            </form>
            <button
              onClick={handleResend}
              disabled={resending}
              className="mt-4 text-sm font-medium text-series-1 hover:underline disabled:opacity-60"
            >
              Resend code
            </button>
            <p className="mt-4 text-center text-sm text-text-secondary">
              <Link href="/" className="font-medium text-series-1 hover:underline">
                Skip for now
              </Link>
            </p>
          </>
        )}
      </Card>
    </div>
  );
}
