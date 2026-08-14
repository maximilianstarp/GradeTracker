"use client";

import { FormEvent, useState } from "react";
import { ApiError, updateMe } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { Card } from "@/components/Card";

export default function AccountPage() {
  const { user, setUser } = useAuth();
  // AuthGate only renders this page once `user` is loaded, so it's safe to
  // seed form state from it directly instead of syncing via an effect.
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (newPassword && newPassword !== newPasswordConfirm) {
      setError("The new passwords don't match");
      return;
    }

    setSubmitting(true);
    try {
      const updated = await updateMe({
        current_password: currentPassword,
        name,
        email,
        ...(newPassword ? { new_password: newPassword } : {}),
      });
      setUser(updated);
      setCurrentPassword("");
      setNewPassword("");
      setNewPasswordConfirm("");
      setSuccess(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to save");
    } finally {
      setSubmitting(false);
    }
  }

  if (!user) return null;

  return (
    <div className="mx-auto max-w-md space-y-6">
      <h1 className="text-2xl font-semibold text-text-primary">Account</h1>

      <Card>
        {error && <p className="mb-3 text-sm text-status-critical">{error}</p>}
        {success && <p className="mb-3 text-sm text-status-good">Changes saved.</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Name">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
            />
          </Field>
          <Field label="Email">
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              required
              className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
            />
          </Field>

          <div className="border-t border-border pt-4">
            <p className="mb-3 text-sm text-text-secondary">
              Change password (optional – leave blank to keep it):
            </p>
            <div className="space-y-3">
              <Field label="New password">
                <input
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  type="password"
                  minLength={8}
                  className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
                />
              </Field>
              <Field label="Confirm new password">
                <input
                  value={newPasswordConfirm}
                  onChange={(e) => setNewPasswordConfirm(e.target.value)}
                  type="password"
                  minLength={8}
                  className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
                />
              </Field>
            </div>
          </div>

          <div className="border-t border-border pt-4">
            <Field label="Current password (required to confirm)">
              <input
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                type="password"
                required
                className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-series-1"
              />
            </Field>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-series-1 px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            Save
          </button>
        </form>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm text-text-secondary">
      <span className="mb-1 block">{label}</span>
      {children}
    </label>
  );
}
