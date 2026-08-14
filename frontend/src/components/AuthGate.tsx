"use client";

import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";
import { useAuth } from "@/lib/AuthContext";
import { Nav } from "@/components/Nav";

const PUBLIC_PATHS = ["/login", "/signup"];

export function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isPublicPath = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    if (loading) return;
    if (!user && !isPublicPath) router.replace("/login");
    if (user && isPublicPath) router.replace("/");
  }, [loading, user, isPublicPath, router]);

  if (loading) return null;
  if (!user && !isPublicPath) return null;
  if (user && isPublicPath) return null;

  return (
    <>
      {user && <Nav />}
      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
    </>
  );
}
