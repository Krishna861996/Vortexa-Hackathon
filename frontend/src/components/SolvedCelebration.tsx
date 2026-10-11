"use client";
import Link from "next/link";
import type { CSSProperties } from "react";
import { QuestIcon } from "./QuestIcon";

export function SolvedCelebration({ next, onClose }: { next: { id: string; title: string } | null; onClose: () => void }) {
  return <section className="solved-celebration" role="status" aria-live="polite">
    <div className="confetti-field" aria-hidden="true">{Array.from({ length: 24 }, (_, i) => <span key={i} style={{ "--x": `${(i * 37) % 100}%`, "--delay": `${(i % 6) * .07}s`, "--turn": `${i % 2 ? 200 : -160}deg`, background: i % 3 === 0 ? "#ffd343" : i % 3 === 1 ? "#6aafff" : "#eaf3ff" } as CSSProperties} />)}</div>
    <div className="flex items-start gap-4"><span className="celebration-medal"><QuestIcon name="medal" className="h-7 w-7" /></span><div className="flex-1"><h2 className="text-lg font-semibold text-white">Challenge complete!</h2><p className="mt-1 text-sm text-slate-300">All visible tests passed. Your progress is saved.</p>{next ? <Link className="mt-4 inline-flex items-center gap-2 text-sm text-lime-200" href={`/challenges/${next.id}`}>Next: {next.title}<QuestIcon name="arrow" className="h-4 w-4" /></Link> : <Link className="mt-4 inline-flex text-sm text-lime-200" href="/">Explore your unlocked challenges →</Link>}</div><button type="button" onClick={onClose} className="celebration-dismiss" aria-label="Dismiss celebration">×</button></div>
  </section>;
}
