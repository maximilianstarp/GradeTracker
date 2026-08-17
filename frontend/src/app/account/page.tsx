"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ApiError, deleteMe, updateMe } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useConfirm } from "@/components/ConfirmDialog";
import { Card } from "@/components/Card";

export default function AccountPage() {
  const { user, setUser, logout } = useAuth();
  const confirm = useConfirm();
  // AuthGate only renders this page once `user` is loaded, so it's safe to
  // seed form state from it directly instead of syncing via an effect.
  const [username, setUsername] = useState(user?.username ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

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
        username,
        email,
        ...(newPassword ? { new_password: newPassword } : {}),
      });
      setUser(updated);
      setEmail(updated.email);
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

  async function handleDelete(e: FormEvent) {
    e.preventDefault();
    setDeleteError(null);

    const confirmed = await confirm({
      title: "Delete account permanently",
      message:
        "This deletes your account and all your Studiengänge, Module and grades. This cannot be undone.",
      confirmLabel: "Delete permanently",
      danger: true,
    });
    if (!confirmed) return;

    setDeleting(true);
    try {
      await deleteMe(deletePassword);
      logout();
    } catch (e) {
      setDeleteError(e instanceof ApiError ? e.message : "Failed to delete account");
      setDeleting(false);
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
          <Field label="Username">
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              pattern="[a-zA-Z0-9_.-]{3,30}"
              title="3-30 characters: letters, numbers, '.', '_' or '-'"
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
            {!user.email_verified && !user.pending_email && (
              <p className="mt-1.5 text-xs text-status-warning">
                Not verified yet.{" "}
                <Link href="/verify-email" className="font-medium underline">
                  Verify now
                </Link>
              </p>
            )}
            {user.pending_email && (
              <p className="mt-1.5 text-xs text-text-secondary">
                Verification pending for <span className="font-medium">{user.pending_email}</span>{" "}
                - your current address stays active until you{" "}
                <Link href="/verify-email" className="font-medium text-series-1 underline">
                  confirm it
                </Link>
                . Save this form with your current email to cancel the change.
              </p>
            )}
            <p className="mt-1.5 text-xs text-text-secondary">
              Changing your email requires confirming a code sent to the new address; nothing
              changes until then.
            </p>
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

      <Card className="border-status-critical/40">
        <h2 className="text-base font-semibold text-status-critical">Danger zone</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Permanently delete your account and all associated data (Studiengänge, Module,
          Kombi-Module, grades and submissions). This action cannot be undone.
        </p>
        {deleteError && <p className="mt-3 text-sm text-status-critical">{deleteError}</p>}
        <form onSubmit={handleDelete} className="mt-4 space-y-3">
          <Field label="Current password">
            <input
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              type="password"
              required
              className="w-full rounded-lg border border-border bg-surface-raised px-3 py-2 text-sm outline-none focus:border-status-critical"
            />
          </Field>
          <button
            type="submit"
            disabled={deleting}
            className="rounded-lg bg-status-critical px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            Delete account permanently
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
