"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useAuth } from "@/components/AuthProvider";
import { QuestIcon, PythonMark } from "@/components/QuestIcon";
import { getSupabase } from "@/lib/supabase";

function nextPath() {
  const next = new URLSearchParams(window.location.search).get("next");
  return next && /^\/(?:challenges\/[a-z0-9-]+|progress)$/.test(next) ? next : "/";
}
export default function LoginPage() {
  const { user, error: setupError } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => { if (user) router.replace(nextPath()); }, [user, router]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const client = getSupabase();
    if (!client) { setError(setupError || "Supabase login is not configured."); return; }
    setBusy(true); setError(""); setNotice("");
    try {
      const credentials = { email: email.trim(), password };
      if (mode === "signup") {
        const { data, error } = await client.auth.signUp({ ...credentials, options: { emailRedirectTo: `${window.location.origin}/login` } });
        if (error) throw error;
        if (!data.session) { setNotice("Check your email for a confirmation link. After confirming, come back here and log in. If an account already exists, use Log in."); setPassword(""); }
      } else {
        const { error } = await client.auth.signInWithPassword(credentials);
        if (error) throw error;
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not reach login. Please try again."); }
    finally { setBusy(false); }
  }
  return <main className="auth-layout">
    <section className="auth-story" aria-labelledby="welcome-heading"><span className="eyebrow"><QuestIcon name="compass" className="h-4 w-4" /> Your next chapter</span><h1 id="welcome-heading">A little code.<br /><span className="hero-blue">A little closer.</span></h1><p>Make room for your next small win. Your challenges, hints, and progress stay with you.</p><div className="auth-path"><span>01 / PRACTICE</span><span>02 / UNDERSTAND</span><span>03 / LEVEL UP</span></div><div className="flex items-center gap-3 text-sm text-slate-400"><PythonMark className="h-9 w-9" />25 Python challenges. Your pace.</div></section>
    <section className="panel auth-card" aria-labelledby="login-heading"><span className="brand-mark"><QuestIcon name="terminal" /></span><h2 id="login-heading">{mode === "login" ? "Welcome back." : "Start your quest."}</h2><p className="mt-2 text-sm leading-6 text-slate-400">{mode === "login" ? "Pick up where you left off." : "Create an account to save every step."}</p>
      <div className="auth-tabs" role="group" aria-label="Account action">{(["login", "signup"] as const).map((item) => <button key={item} type="button" aria-pressed={mode === item} disabled={busy} onClick={() => { setMode(item); setError(""); setNotice(""); }} className={mode === item ? "active" : ""}>{item === "login" ? "Log in" : "Create account"}</button>)}</div>
      <form onSubmit={submit} className="space-y-5"><div><label htmlFor="email" className="auth-label">Email address</label><input className="auth-input" id="email" name="email" type="email" autoComplete="email" placeholder="you@example.com" required maxLength={254} value={email} onChange={(event) => setEmail(event.target.value)} disabled={busy} /></div><div><label htmlFor="password" className="auth-label">Password</label><input className="auth-input" id="password" name="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={mode === "signup" ? 8 : 1} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} disabled={busy} aria-describedby={mode === "signup" ? "password-help" : undefined} />{mode === "signup" ? <p id="password-help" className="mt-2 text-xs text-slate-400">Use at least 8 characters.</p> : null}</div>
        {error || setupError ? <p role="alert" className="rounded-lg border border-rose-300/20 bg-rose-300/5 p-3 text-sm text-rose-200">{error || setupError}</p> : null}
        {notice ? <p role="status" className="rounded-lg border border-sky-300/20 bg-sky-300/5 p-3 text-sm leading-6 text-sky-100">{notice}</p> : null}
        <button className="primary-button w-full" type="submit" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Continue your quest" : "Create my account"}<QuestIcon name="arrow" className="h-4 w-4" /></button>
      </form><p className="mt-6 text-center text-xs leading-6 text-slate-500">Secure login with Supabase. Your progress belongs to your account.</p><Link href="/" className="mt-5 block text-center text-sm text-slate-400 hover:text-white">Browse the challenges first →</Link>
    </section>
  </main>;
}
