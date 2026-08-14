import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/lib/AuthContext";
import { AuthGate } from "@/components/AuthGate";
import { ConfirmProvider } from "@/components/ConfirmDialog";
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
  description: "Keep track of degree programs, modules, grades and exam admissions.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-page">
        <AuthProvider>
          <ConfirmProvider>
            <AuthGate>{children}</AuthGate>
          </ConfirmProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
