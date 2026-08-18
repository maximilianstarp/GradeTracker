// Client Component despite being fully static: rendered in RootLayout as a
// sibling *after* the AuthGate client-component subtree closes. A plain
// Server Component in that position triggers a hydration bug in this
// Next/React version - the whole subtree above it gets duplicated in the
// DOM after hydration (confirmed by bisection; not just a style nit).
"use client";

import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border py-4 text-center text-xs text-text-muted">
      <Link href="/impressum" className="hover:text-text-secondary hover:underline">
        Impressum
      </Link>
      <span className="mx-2">·</span>
      <Link href="/datenschutz" className="hover:text-text-secondary hover:underline">
        Datenschutz
      </Link>
    </footer>
  );
}
