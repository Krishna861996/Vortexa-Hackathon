"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { QuestIcon } from "./QuestIcon";
import { useAuth } from "./AuthProvider";
import { getSupabase } from "@/lib/supabase";
import { useState } from "react";

export function SiteHeader() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function signOut() {
    setBusy(true); setError("");
    try { const result = await getSupabase()?.auth.signOut({ scope: "local" }); if (result?.error) throw result.error; }
    catch { setError("Could not log out. Please retry."); }
    finally { setBusy(false); }
  }
  return (
    <header className="site-header">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-2 px-5 py-4 sm:gap-4 sm:px-8 lg:px-10">
        <Link href="/" className="flex min-w-0 items-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-lime-300 sm:gap-3" aria-label="CodeQuest AI home">
          <span className="brand-mark overflow-hidden" aria-hidden="true">
            <Image
              src="/logo-icon.png"
              alt="CodeQuest Logo"
              width={32}
              height={32}
              className="h-7 w-7 object-contain"
              priority
            />
          </span>
          <span className="whitespace-nowrap text-sm font-bold tracking-[-0.04em] text-white sm:text-xl">CodeQuest <span className="text-lime-300">AI</span></span>
        </Link>
        <nav aria-label="Main navigation" className="flex items-center gap-1 sm:gap-2">
          <Link href="/" aria-current={pathname === "/" || pathname.startsWith("/challenges/") ? "page" : undefined} className={`nav-link ${pathname === "/" || pathname.startsWith("/challenges/") ? "nav-link-active" : ""}`}><QuestIcon name="compass" className="hidden h-4 w-4 sm:block" />Challenges</Link>
          <Link href="/progress" aria-current={pathname === "/progress" ? "page" : undefined} className={`nav-link ${pathname === "/progress" ? "nav-link-active" : ""}`}><QuestIcon name="layers" className="hidden h-4 w-4 sm:block" />Progress</Link>
          {user ? <button className="nav-link" onClick={signOut} disabled={busy} title={user.email}>{busy ? "Exiting…" : "Log out"}</button> : <Link href="/login" className={`nav-link ${pathname === "/login" ? "nav-link-active" : ""}`}>Log in</Link>}
        </nav>
      </div>
      {error ? <p role="alert" className="px-5 pb-3 text-center text-sm text-rose-200">{error}</p> : null}
    </header>
  );
}
