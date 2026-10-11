"use client";
import Link from "next/link";
import type { CSSProperties } from "react";
import { QuestIcon } from "./QuestIcon";

export function SolvedCelebration({
  next,
  onClose,
  earnedXp,
  soloBonus,
  stars,
  levelName,
}: {
  next: { id: string; title: string } | null;
  onClose: () => void;
  earnedXp?: number;
  soloBonus?: boolean;
  stars?: number;
  levelName?: string;
}) {
  return (
    <section className="solved-celebration" role="status" aria-live="polite">
      <div className="confetti-field" aria-hidden="true">
        {Array.from({ length: 24 }, (_, i) => (
          <span
            key={i}
            style={
              {
                "--x": `${(i * 37) % 100}%`,
                "--delay": `${(i % 6) * 0.07}s`,
                "--turn": `${i % 2 ? 200 : -160}deg`,
                background: i % 3 === 0 ? "#ffd343" : i % 3 === 1 ? "#6aafff" : "#eaf3ff",
              } as CSSProperties
            }
          />
        ))}
      </div>
      <div className="flex items-start gap-4">
        <span className="celebration-medal">
          <QuestIcon name="medal" className="h-7 w-7" />
        </span>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-white">Mission Accomplished!</h2>
            {stars ? (
              <span className="text-sm font-bold text-amber-300">
                {"★".repeat(stars)}
              </span>
            ) : null}
          </div>
          <p className="mt-1 text-sm text-slate-300">
            All visible tests passed. Your progress and learning points have been saved.
          </p>

          {/* Gamification XP & Solo Twist Card */}
          {earnedXp ? (
            <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-lime-300/20 bg-lime-400/10 p-2.5 text-xs">
              <span className="font-mono font-bold text-lime-300">
                +{earnedXp} XP EARNED
              </span>
              {soloBonus ? (
                <span className="rounded bg-amber-400/20 px-2 py-0.5 font-bold text-amber-200">
                  🌟 Solo Maverick (+50 Bonus XP for 0 Hints!)
                </span>
              ) : null}
              {levelName ? (
                <span className="text-slate-400">· Rank: {levelName}</span>
              ) : null}
            </div>
          ) : null}

          {next ? (
            <Link className="mt-4 inline-flex items-center gap-2 text-sm text-lime-200" href={`/challenges/${next.id}`}>
              Next Mission: {next.title}
              <QuestIcon name="arrow" className="h-4 w-4" />
            </Link>
          ) : (
            <Link className="mt-4 inline-flex text-sm text-lime-200" href="/">
              Explore your unlocked missions →
            </Link>
          )}
        </div>
        <button type="button" onClick={onClose} className="celebration-dismiss" aria-label="Dismiss celebration">
          ×
        </button>
      </div>
    </section>
  );
}
