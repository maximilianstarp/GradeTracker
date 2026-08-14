import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Grade Tracker",
  description: "Studiengänge, Module, Noten und Klausurzulassungen im Blick behalten.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="de"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-page">
        <Nav />
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">{children}</main>
        <footer className="border-t border-border px-6 py-4 text-center text-xs text-text-muted">
          Grade Tracker · lokal & selbstgehostet
        </footer>
      </body>
    </html>
  );
}
