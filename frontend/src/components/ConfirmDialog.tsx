"use client";

import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";

interface ConfirmOptions {
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

type ConfirmFn = (options: ConfirmOptions | string) => Promise<boolean>;

const ConfirmContext = createContext<ConfirmFn | null>(null);

interface PendingConfirm extends ConfirmOptions {
  resolve: (value: boolean) => void;
}

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<PendingConfirm | null>(null);

  const confirm = useCallback<ConfirmFn>((options) => {
    const opts = typeof options === "string" ? { message: options } : options;
    return new Promise<boolean>((resolve) => setPending({ ...opts, resolve }));
  }, []);

  function settle(result: boolean) {
    pending?.resolve(result);
    setPending(null);
  }

  useEffect(() => {
    if (!pending) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") settle(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pending]);

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {pending && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={() => settle(false)}
        >
          <div
            role="alertdialog"
            aria-modal="true"
            className="w-full max-w-sm rounded-xl border border-border bg-surface-raised p-5 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            {pending.title && (
              <h2 className="text-base font-semibold text-text-primary">{pending.title}</h2>
            )}
            <p className="mt-1 text-sm text-text-secondary">{pending.message}</p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => settle(false)}
                className="rounded-lg px-3 py-1.5 text-sm text-text-secondary hover:bg-text-muted/10"
              >
                {pending.cancelLabel ?? "Abbrechen"}
              </button>
              <button
                onClick={() => settle(true)}
                autoFocus
                className={`rounded-lg px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 ${
                  pending.danger ? "bg-status-critical" : "bg-series-1"
                }`}
              >
                {pending.confirmLabel ?? "Bestätigen"}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error("useConfirm must be used within ConfirmProvider");
  return ctx;
}
