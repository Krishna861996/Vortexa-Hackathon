"use client";
import { createContext, useContext, useEffect, useState } from "react";
import type { User } from "@supabase/supabase-js";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import { StatusState } from "./StatusState";

const AuthContext = createContext<{ user: User | null; error: string }>({ user: null, error: "" });
export const useAuth = () => useContext(AuthContext);
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const client = getSupabase();
    if (!client) { setError("Login is not configured. Add the Supabase public settings to frontend/.env.local."); setLoading(false); return; }
    let active = true;
    const { data: { subscription } } = client.auth.onAuthStateChange((_event, session) => {
      if (active) { setUser(session?.user ?? null); setLoading(false); }
    });
    client.auth.getSession().then(({ data, error: sessionError }) => {
      if (!active) return;
      setUser(data.session?.user ?? null);
      if (sessionError) setError("Your previous session could not be restored. Please log in again.");
      setLoading(false);
    }).catch(() => { if (active) { setError("Could not restore your login. Please try again."); setLoading(false); } });
    return () => { active = false; subscription.unsubscribe(); };
  }, []);
  if (loading) return <main className="mx-auto max-w-7xl p-8" role="status"><div className="skeleton h-64 rounded-2xl" /><p className="mt-4 text-sm text-slate-400">Getting your workspace ready…</p></main>;
  // Clear the previous account's component state on login/logout.
  return <AuthContext.Provider value={{ user, error }}><div key={user?.id ?? "guest"}>{children}</div></AuthContext.Provider>;
}
export function RequireLogin({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const pathname = usePathname();
  if (!user) return <main className="mx-auto max-w-3xl px-5 py-16"><StatusState title="Your own learning journey" description="Log in to run challenges, reveal hints, and keep your progress across devices." action={<Link className="primary-button" href={`/login?next=${encodeURIComponent(pathname)}`}>Log in to continue →</Link>} /></main>;
  return children;
}
