"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { ThemeToggle } from "@/components/ThemeToggle";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/studiengaenge", label: "Programs" },
  { href: "/module", label: "Modules" },
  { href: "/kombimodule", label: "Combined Modules" },
];

export function Nav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
        <span className="text-base font-semibold text-text-primary">🎓 Grade Tracker</span>
        <nav className="flex flex-1 gap-1">
          {LINKS.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-series-1/10 text-series-1"
                    : "text-text-secondary hover:bg-text-muted/10 hover:text-text-primary"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-1 text-sm">
          <ThemeToggle />
          <Link
            href="/account"
            className={`rounded-lg px-3 py-1.5 font-medium transition-colors ${
              pathname === "/account"
                ? "bg-series-1/10 text-series-1"
                : "text-text-secondary hover:bg-text-muted/10 hover:text-text-primary"
            }`}
          >
            {user?.name}
          </Link>
          <button
            onClick={logout}
            className="rounded-lg px-3 py-1.5 font-medium text-text-secondary hover:bg-text-muted/10 hover:text-text-primary"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
