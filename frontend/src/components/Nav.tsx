"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/studiengaenge", label: "Studiengänge" },
  { href: "/module", label: "Module" },
  { href: "/kombimodule", label: "Kombi-Module" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-4">
        <span className="text-base font-semibold text-text-primary">🎓 Grade Tracker</span>
        <nav className="flex gap-1">
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
      </div>
    </header>
  );
}
