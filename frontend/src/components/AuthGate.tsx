"use client";

import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";
import { Nav } from "@/components/Nav";

// Only reachable while logged out - a logged-in user gets bounced to "/".
const AUTH_ONLY_PATHS = ["/login", "/signup", "/forgot-password", "/reset-password"];
// Reachable regardless of auth state, no redirect either way (e.g. legal
// pages a logged-out visitor must be able to read too).
const ALWAYS_PUBLIC_PATHS = ["/impressum", "/datenschutz"];

export function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isAuthOnlyPath = AUTH_ONLY_PATHS.includes(pathname);
  const isAlwaysPublicPath = ALWAYS_PUBLIC_PATHS.includes(pathname);
  const requiresLogin = !isAuthOnlyPath && !isAlwaysPublicPath;

  useEffect(() => {
    if (loading) return;
    if (!user && requiresLogin) router.replace("/login");
    if (user && isAuthOnlyPath) router.replace("/");
  }, [loading, user, requiresLogin, isAuthOnlyPath, router]);

  if (loading) return null;
  if (!user && requiresLogin) return null;
  if (user && isAuthOnlyPath) return null;

  return (
    <>
      {user && <Nav />}
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
    </>
  );
}
