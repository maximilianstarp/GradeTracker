"use client";

import Link from "next/link";
import { Suspense, FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ApiError, resetPassword } from "@/lib/api";
import { Card } from "@/components/Card";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPassword !== newPasswordConfirm) {
      setError("The new passwords don't match");
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword({ email, code, new_password: newPassword });
      setSuccess(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to reset password");
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
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Set a new password</h2>
        {success ? (
          <>
            <p className="text-sm text-status-good">
              Your password has been reset. You can log in with it now.
            </p>
            <button
              onClick={() => router.replace("/login")}
              className="mt-4 w-full rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90"
            >
              Go to log in
            </button>
          </>
        ) : (
          <>
            <p className="mb-4 text-sm text-text-secondary">
              Enter the code we emailed you along with your new password.
            </p>
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
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                placeholder="6-digit code"
                minLength={6}
                maxLength={6}
                required
                className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-center text-lg tracking-[0.3em] outline-none focus:border-series-1"
              />
              <input
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                type="password"
                placeholder="New password (min. 8 characters)"
                minLength={8}
                required
                className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              />
              <input
                value={newPasswordConfirm}
                onChange={(e) => setNewPasswordConfirm(e.target.value)}
                type="password"
                placeholder="Confirm new password"
                minLength={8}
                required
                className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              />
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
              >
                Reset password
              </button>
            </form>
          </>
        )}
        <p className="mt-4 text-center text-sm text-text-secondary">
          <Link href="/login" className="font-medium text-series-1 hover:underline">
            Back to log in
          </Link>
        </p>
      </Card>
    </div>
  );
}
