"use client";

import Link from "next/link";
import { RequireLogin } from "@/components/AuthProvider";
import { useEffect, useState } from "react";
import { QuestIcon, challengeIcons, type IconName } from "@/components/QuestIcon";
import { StatusState } from "@/components/StatusState";
import { api, formatConcept, type ChallengeSummary, type ConceptStatus, type LearnerProgress } from "@/lib/api";

const conceptIcons: Record<string, IconName> = { functions: "terminal", arithmetic: "spark", conditionals: "branch", strings: "text", loops: "loop", lists: "list", booleans: "diamond", modulo: "compass", logic: "layers" };
const statusIcons: Record<ConceptStatus, IconName> = { "not started": "flag", practicing: "compass", improving: "mountain", demonstrated: "medal" };
type LoadState = "loading" | "ready" | "error";
const statusStyle: Record<ConceptStatus, string> = {
  "not started": "border-white/10 bg-white/[0.04] text-slate-300",
  practicing: "border-sky-300/20 bg-sky-300/10 text-sky-200",
  improving: "border-amber-300/20 bg-amber-300/10 text-amber-200",
  demonstrated: "border-lime-300/20 bg-lime-300/10 text-lime-200",
};

export default function ProgressPage() {
  return <RequireLogin><ProgressContent /></RequireLogin>;
}

function ProgressContent() {
  const [progress, setProgress] = useState<LearnerProgress | null>(null);
  const [challenges, setChallenges] = useState<ChallengeSummary[]>([]);
  const [status, setStatus] = useState<LoadState>("loading");
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([api.getProgress(controller.signal), api.listChallenges(controller.signal)])
      .then(([learnerProgress, library]) => {
        setProgress(learnerProgress);
        setChallenges(library);
        setStatus("ready");
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "Could not load progress.");
        setStatus("error");
      });
    return () => controller.abort();
  }, [refreshKey]);

  const solvedIds = new Set(progress?.challenges.filter((item) => item.solved).map((item) => item.challenge_id) ?? []);
  const completed = challenges.filter((challenge) => solvedIds.has(challenge.id));

  return (
    <main className="mx-auto w-full max-w-7xl px-5 pb-20 pt-12 sm:px-8 sm:pt-16 lg:px-10">
      <span className="eyebrow">Your journey</span>
      <div className="mt-4 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-4xl font-bold tracking-[-0.055em] text-white sm:text-5xl">Every mission counts.</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Track your XP milestones, unlocked achievement badges, and demonstrated Python skills.
          </p>
        </div>
        <Link href="/" className="secondary-button self-start sm:self-auto">Explore missions <span aria-hidden="true">↗</span></Link>
      </div>

      {status === "loading" ? <div className="mt-10 space-y-6"><div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="skeleton h-34 rounded-2xl" />)}</div><div className="skeleton h-80 rounded-2xl" /></div> : null}
      {status === "error" ? <div className="mt-10"><StatusState tone="error" title="Progress could not load" description={error} action={<button type="button" className="secondary-button" onClick={() => { setStatus("loading"); setRefreshKey((key) => key + 1); }}>Try again</button>} /></div> : null}
      {status === "ready" && progress ? <>
        {/* Gamification Level & XP Milestone Card */}
        <section className="mt-8 rounded-2xl border border-lime-300/20 bg-gradient-to-r from-[#0d1620] via-[#091017] to-[#0c1815] p-6 sm:p-8">
          <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-lime-400/20 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-lime-300">
                  Level {progress.current_level ?? 1}
                </span>
                <span className="text-sm font-semibold text-slate-300">
                  {progress.level_name ?? "Novice Coder"}
                </span>
                {progress.daily_streak ? (
                  <span className="ml-2 rounded-md bg-orange-400/20 px-2 py-0.5 text-xs font-bold text-orange-300">
                    🔥 {progress.daily_streak} Day Streak
                  </span>
                ) : null}
              </div>
              <h2 className="mt-2 text-3xl font-extrabold text-white">
                {progress.total_xp ?? 0} <span className="text-lg font-normal text-slate-400">Total XP</span>
              </h2>
            </div>
            <div className="w-full sm:max-w-xs">
              <div className="flex justify-between text-xs font-medium text-slate-400">
                <span>Progress to Next Rank</span>
                <span>{progress.level_progress_pct ?? 0}%</span>
              </div>
              <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-lime-400 to-emerald-400 transition-all duration-500"
                  style={{ width: `${progress.level_progress_pct ?? 0}%` }}
                />
              </div>
              <p className="mt-2 text-right text-xs text-slate-400">
                Next Rank Target: {progress.next_level_xp ?? 150} XP
              </p>
            </div>
          </div>
        </section>

        {/* Stats Row */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="panel p-6">
            <p className="text-xs font-bold uppercase tracking-[.13em] text-slate-400">
              <QuestIcon name="flag" className="mb-4 h-7 w-7 text-lime-300" />Missions Conquered
            </p>
            <p className="mt-4 text-4xl font-bold tracking-tight text-white">
              {progress.solved_challenges}<span className="ml-2 text-lg font-medium text-slate-500">/ {challenges.length}</span>
            </p>
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-lime-300" style={{ width: `${challenges.length ? Math.round((progress.solved_challenges / challenges.length) * 100) : 0}%` }} />
            </div>
          </div>
          <div className="panel p-6">
            <p className="text-xs font-bold uppercase tracking-[.13em] text-slate-400">
              <QuestIcon name="terminal" className="mb-4 h-7 w-7 text-lime-300" />Code runs
            </p>
            <p className="mt-4 text-4xl font-bold tracking-tight text-white">{progress.total_attempts}</p>
            <p className="mt-3 text-xs text-slate-500">Every attempt sharpens your skills.</p>
          </div>
          <div className="panel p-6">
            <p className="text-xs font-bold uppercase tracking-[.13em] text-slate-400">
              <QuestIcon name="compass" className="mb-4 h-7 w-7 text-lime-300" />Concepts practiced
            </p>
            <p className="mt-4 text-4xl font-bold tracking-tight text-white">{progress.concepts_practiced.length}</p>
            <p className="mt-3 text-xs text-slate-500">Across your submitted missions.</p>
          </div>
        </div>

        {/* Achievement Badges Showcase */}
        {progress.badges && progress.badges.length > 0 ? (
          <section className="mt-8 panel p-6 sm:p-8" aria-labelledby="badges-heading">
            <div className="flex items-center justify-between">
              <div>
                <span className="eyebrow text-amber-300">Gamification</span>
                <h2 id="badges-heading" className="mt-2 text-2xl font-semibold tracking-tight text-white">
                  Achievement Badges
                </h2>
              </div>
              <span className="rounded-full bg-amber-400/15 px-3 py-1 text-xs font-bold text-amber-300">
                {progress.badges.filter((b) => b.unlocked).length} / {progress.badges.length} Unlocked
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-400">
              Unlock badges by mastering challenges, completing daily challenges, and solving missions solo with zero hints!
            </p>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {progress.badges.map((b) => (
                <div
                  key={b.id}
                  className={`flex flex-col justify-between rounded-xl border p-4 transition-all ${
                    b.unlocked
                      ? "border-amber-400/30 bg-[#0c121b] shadow-[0_0_15px_rgba(251,191,36,0.06)]"
                      : "border-white/5 bg-white/[0.02] opacity-50"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className={`flex h-10 w-10 items-center justify-center rounded-lg ${b.unlocked ? "bg-amber-400/15 text-amber-300" : "bg-white/5 text-slate-500"}`}>
                        <QuestIcon name={(b.icon as IconName) ?? "medal"} className="h-5 w-5" />
                      </span>
                      {b.unlocked ? (
                        <span className="rounded bg-emerald-400/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-300">
                          Unlocked ✓
                        </span>
                      ) : (
                        <span className="text-[10px] uppercase tracking-wider text-slate-500">
                          Locked 🔒
                        </span>
                      )}
                    </div>
                    <h3 className={`mt-3 font-bold ${b.unlocked ? "text-white" : "text-slate-400"}`}>
                      {b.name}
                    </h3>
                    <p className="mt-1 text-xs leading-5 text-slate-400">
                      {b.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {/* Progress Map Roadmap */}
        {progress.progress_map && progress.progress_map.length > 0 ? (
          <section className="mt-8 panel p-6 sm:p-8" aria-labelledby="map-heading">
            <div className="flex items-center justify-between">
              <div>
                <span className="eyebrow text-lime-300">Roadmap</span>
                <h2 id="map-heading" className="mt-2 text-2xl font-semibold tracking-tight text-white">
                  Mission Progress Map
                </h2>
              </div>
              <span className="text-xs text-slate-500">
                Solve without hints to earn 3 stars ⭐⭐⭐
              </span>
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {progress.progress_map.map((node) => (
                <Link
                  key={node.challenge_id}
                  href={node.status === "locked" ? "#map-heading" : `/challenges/${node.challenge_id}`}
                  className={`flex flex-col justify-between rounded-xl border p-4 transition-all ${
                    node.status === "locked"
                      ? "cursor-not-allowed border-white/5 bg-white/[0.02] opacity-60"
                      : node.status === "completed"
                      ? "border-emerald-500/30 bg-emerald-500/[0.06] hover:border-emerald-400/50"
                      : "border-lime-400/30 bg-lime-400/10 hover:border-lime-300/60"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between text-xs font-bold">
                      <span className="text-slate-400">MISSION {String(node.mission_number).padStart(2, "0")}</span>
                      <span className={`capitalize ${node.difficulty === "beginner" ? "text-emerald-300" : node.difficulty === "easy" ? "text-sky-300" : node.difficulty === "medium" ? "text-amber-300" : "text-rose-300"}`}>
                        {node.difficulty}
                      </span>
                    </div>
                    <h3 className="mt-2 font-bold text-white">{node.title}</h3>
                  </div>
                  <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-xs">
                    <span className="text-amber-300">
                      {node.status === "completed" ? (
                        <>
                          {"★".repeat(node.stars || 3)}
                          {"☆".repeat(Math.max(0, 3 - (node.stars || 3)))}
                        </>
                      ) : (
                        <span className="capitalize text-slate-400">{node.status}</span>
                      )}
                    </span>
                    <span className="font-mono text-lime-300">+{node.xp_earned || 100} XP</span>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        ) : null}

        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,.92fr)]">
          <section className="panel p-6 sm:p-8" aria-labelledby="completed-heading">
            <span className="eyebrow">Milestones</span>
            <div className="mt-4 flex items-center justify-between gap-4">
              <h2 id="completed-heading" className="text-2xl font-semibold tracking-tight text-white">Completed missions</h2>
              <span className="text-xs text-slate-500">{completed.length} complete</span>
            </div>
            {completed.length ? (
              <div className="mt-6 space-y-3">
                {completed.map((challenge) => (
                  <Link key={challenge.id} href={`/challenges/${challenge.id}`} className="group flex items-center justify-between gap-4 rounded-xl border border-white/10 bg-[#0c121b] p-4 transition-colors hover:border-lime-300/30">
                    <div className="flex min-w-0 items-center gap-4">
                      <span className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-lime-300/12 text-lime-300" aria-hidden="true">
                        <QuestIcon name={challengeIcons[challenge.id] ?? "medal"} />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-white group-hover:text-lime-200">{challenge.title}</p>
                        <p className="mt-1 text-xs capitalize text-slate-400">{challenge.difficulty} · {challenge.concept_tags.map(formatConcept).join(", ")}</p>
                      </div>
                    </div>
                    <span className="flex-none text-lime-300" aria-hidden="true">→</span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="mt-6 rounded-xl border border-dashed border-white/15 bg-white/[0.025] p-8 text-center">
                <p className="font-semibold text-white">Your first win is waiting</p>
                <p className="mt-2 text-sm leading-6 text-slate-400">Complete a mission to see it appear here.</p>
                <Link href="/" className="primary-button mt-5">Choose a mission</Link>
              </div>
            )}
          </section>

          <section className="panel p-6 sm:p-8" aria-labelledby="recommendations-heading">
            <span className="eyebrow">Next practice</span>
            <h2 id="recommendations-heading" className="mt-4 text-2xl font-semibold tracking-tight text-white">Recommended missions</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Suggestions adapt to repeated errors and recurring patterns across your attempts.</p>
            {progress.recommendations.length ? (
              <div className="mt-6 space-y-3">
                {progress.recommendations.map((item) => (
                  <div key={item.concept + item.challenge_id} className="rounded-xl border border-lime-300/15 bg-lime-300/[0.045] p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-bold uppercase tracking-[.12em] text-lime-300">{formatConcept(item.concept)} · {item.repeated_category}</p>
                      {item.adapted_for ? <span className="rounded-md bg-amber-400/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-300">Adapted for you</span> : null}
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-200">{item.reason}</p>
                    <Link href={`/challenges/${item.challenge_id}`} className="mt-3 inline-flex text-sm font-bold text-lime-300 hover:text-lime-200">
                      Practice {item.challenge_title} <span className="ml-2" aria-hidden="true">→</span>
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-6 rounded-xl border border-dashed border-white/15 bg-white/[0.025] p-5 text-sm leading-6 text-slate-400">
                No repeated mistake pattern yet. Focused suggestions appear when your attempts encounter recurring challenges.
              </div>
            )}
          </section>
        </div>

        {progress.recurring_mistakes && progress.recurring_mistakes.length > 0 ? (
          <section className="mt-8 panel p-6 sm:p-8 border-amber-500/20 bg-amber-500/[0.03]">
            <span className="eyebrow text-amber-300">Adaptive Feedback</span>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white">Detected recurring patterns</h2>
            <p className="mt-2 text-sm text-slate-300">We analyze your submissions to detect repeated stumbling blocks (like off-by-one bounds or empty input handling) and adapt upcoming recommendations to help you overcome them.</p>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {progress.recurring_mistakes.map((m) => (
                <div key={m.mistake_type} className="rounded-xl border border-amber-400/20 bg-[#0c121b] p-5">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-semibold text-amber-200">{m.label}</h3>
                    <span className="rounded-full bg-amber-400/15 px-2.5 py-0.5 text-xs font-mono font-medium text-amber-300">{m.occurrences} attempts</span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-300">{m.description}</p>
                  <div className="mt-3 rounded-lg border border-amber-400/15 bg-amber-400/[0.08] p-3 text-xs leading-5 text-amber-100">
                    <strong className="text-amber-300">How to master: </strong>{m.focus_advice}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <section className="mt-8" aria-labelledby="concept-heading">
          <span className="eyebrow">Your toolkit</span>
          <h2 id="concept-heading" className="mt-4 text-2xl font-semibold tracking-tight text-white">Concept progress</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Track your demonstrated skills by concept. Full passes and distinct solutions unlock verified demonstrated skills.</p>
          <div className="mt-5 rounded-2xl border border-white/10 bg-[#10151d] p-5 text-xs leading-6 text-slate-300 sm:text-sm">
            <p><strong className="text-white">Not started:</strong> no attempts. <strong className="text-white">Practicing:</strong> attempts without a sustained pass pattern.</p>
            <p><strong className="text-white">Improving:</strong> at least two attempts and a full pass on the latest attempt. <strong className="text-white">Demonstrated:</strong> at least three attempts, two different passing solutions, and two full passes among the latest three attempts.</p>
          </div>
          {progress.concepts.length ? (
            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {progress.concepts.map((item) => (
                <article key={item.concept} className="panel p-5 sm:p-6">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
                      <QuestIcon name={conceptIcons[item.concept] ?? "layers"} className="h-5 w-5 text-lime-300" />
                      {formatConcept(item.concept)}
                    </h3>
                    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold capitalize ${statusStyle[item.status]}`}>
                      <QuestIcon name={statusIcons[item.status]} className="h-3.5 w-3.5" />{item.status}
                    </span>
                  </div>
                  <p className="mt-4 text-sm text-slate-300"><strong className="text-white">{item.passed_attempts}</strong> full passes in <strong className="text-white">{item.attempts}</strong> attempts</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{item.distinct_passing_solutions} different passing solutions · {item.completed_challenges} of {item.available_challenges} challenges complete</p>
                  {item.demonstrated_skills && item.demonstrated_skills.length > 0 ? (
                    <div className="mt-4 border-t border-white/10 pt-4">
                      <p className="text-xs font-bold uppercase tracking-[.12em] text-slate-500">Demonstrated skills</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {item.demonstrated_skills.map((skill) => (
                          <span key={skill} className="rounded-md border border-lime-300/20 bg-lime-300/10 px-2 py-0.5 text-xs text-lime-200">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : null}
        </section>
      </> : null}
    </main>
  );
}
