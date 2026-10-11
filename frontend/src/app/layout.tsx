import type { Metadata } from "next";
import { SiteHeader } from "@/components/SiteHeader";
import { ScrollEffects } from "@/components/ScrollEffects";
import { AuthProvider } from "@/components/AuthProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeQuest AI — Python practice",
  description: "Practice Python one challenge at a time and track your progress.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider><div className="min-h-screen">
          <SiteHeader />
          <ScrollEffects />
          {children}
          <footer className="border-t border-white/8 px-5 py-8 text-center text-xs text-slate-500">
            CodeQuest AI · Practice Python at your own pace
          </footer>
        </div></AuthProvider>
      </body>
    </html>
  );
}
