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
      <div className="mt-4 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><h1 className="text-4xl font-bold tracking-[-0.055em] text-white sm:text-5xl">Every step counts.</h1><p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">See what you have completed and which Python concepts you have practiced.</p></div><Link href="/" className="secondary-button self-start sm:self-auto">Explore challenges <span aria-hidden="true">↗</span></Link></div>

      {status === "loading" ? <div className="mt-10 space-y-6"><div className="grid gap-4 sm:grid-cols-3">{[1, 2, 3].map((item) => <div key={item} className="skeleton h-34 rounded-2xl" />)}</div><div className="skeleton h-80 rounded-2xl" /></div> : null}
      {status === "error" ? <div className="mt-10"><StatusState tone="error" title="Progress could not load" description={error} action={<button type="button" className="secondary-button" onClick={() => { setStatus("loading"); setRefreshKey((key) => key + 1); }}>Try again</button>} /></div> : null}
      {status === "ready" && progress ? <>
        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          <div className="panel p-6"><p className="text-xs font-bold uppercase tracking-[.13em] text-slate-400"><QuestIcon name="flag" className="mb-4 h-7 w-7 text-lime-300" />Challenges complete</p><p className="mt-4 text-4xl font-bold tracking-tight text-white">{progress.solved_challenges}<span className="ml-2 text-lg font-medium text-slate-500">/ {challenges.length}</span></p><div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-lime-300" style={{ width: `${challenges.length ? Math.round((progress.solved_challenges / challenges.length) * 100) : 0}%` }} /></div></div>
          <div className="panel p-6"><p className="text-xs font-bold uppercase tracking-[.13em] text-slate-400"><QuestIcon name="terminal" className="mb-4 h-7 w-7 text-lime-300" />Code runs</p><p className="mt-4 text-4xl font-bold tracking-tight text-white">{progress.total_attempts}</p><p className="mt-3 text-xs text-slate-500">Every try helps you learn.</p></div>
          <div className="panel p-6"><p className="text-xs font-bold uppercase tracking-[.13em] text-slate-400"><QuestIcon name="compass" className="mb-4 h-7 w-7 text-lime-300" />Concepts practiced</p><p className="mt-4 text-4xl font-bold tracking-tight text-white">{progress.concepts_practiced.length}</p><p className="mt-3 text-xs text-slate-500">Across your submitted challenges.</p></div>
        </div>

        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,.92fr)]">
          <section className="panel p-6 sm:p-8" aria-labelledby="completed-heading"><span className="eyebrow">Milestones</span><div className="mt-4 flex items-center justify-between gap-4"><h2 id="completed-heading" className="text-2xl font-semibold tracking-tight text-white">Completed challenges</h2><span className="text-xs text-slate-500">{completed.length} complete</span></div>
            {completed.length ? <div className="mt-6 space-y-3">{completed.map((challenge) => <Link key={challenge.id} href={`/challenges/${challenge.id}`} className="group flex items-center justify-between gap-4 rounded-xl border border-white/10 bg-[#0c121b] p-4 transition-colors hover:border-lime-300/30"><div className="flex min-w-0 items-center gap-4"><span className="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-lime-300/12 text-lime-300" aria-hidden="true"><QuestIcon name={challengeIcons[challenge.id] ?? "medal"} /></span><div className="min-w-0"><p className="truncate font-semibold text-white group-hover:text-lime-200">{challenge.title}</p><p className="mt-1 text-xs capitalize text-slate-400">{challenge.difficulty} · {challenge.concept_tags.map(formatConcept).join(", ")}</p></div></div><span className="flex-none text-lime-300" aria-hidden="true">→</span></Link>)}</div> : <div className="mt-6 rounded-xl border border-dashed border-white/15 bg-white/[0.025] p-8 text-center"><p className="font-semibold text-white">Your first win is waiting</p><p className="mt-2 text-sm leading-6 text-slate-400">Complete a challenge to see it appear here.</p><Link href="/" className="primary-button mt-5">Choose a challenge</Link></div>}
          </section>
          <section className="panel p-6 sm:p-8" aria-labelledby="recommendations-heading"><span className="eyebrow">Next practice</span><h2 id="recommendations-heading" className="mt-4 text-2xl font-semibold tracking-tight text-white">Recommended challenges</h2><p className="mt-2 text-sm leading-6 text-slate-400">Suggestions appear when two different code versions fail with the same result category for a concept.</p>
            {progress.recommendations.length ? <div className="mt-6 space-y-3">{progress.recommendations.map((item) => <div key={item.concept} className="rounded-xl border border-lime-300/15 bg-lime-300/[0.045] p-4"><p className="text-xs font-bold uppercase tracking-[.12em] text-lime-300">{formatConcept(item.concept)} · {item.repeated_category}</p><p className="mt-2 text-sm leading-6 text-slate-200">{item.reason}</p><Link href={`/challenges/${item.challenge_id}`} className="mt-3 inline-flex text-sm font-bold text-lime-300 hover:text-lime-200">Practice {item.challenge_title} <span className="ml-2" aria-hidden="true">→</span></Link></div>)}</div> : <div className="mt-6 rounded-xl border border-dashed border-white/15 bg-white/[0.025] p-5 text-sm leading-6 text-slate-400">No repeated mistake pattern yet. A focused suggestion appears when your two latest attempts for a concept fail in the same way with different code.</div>}
          </section>
        </div>

        <section className="mt-8" aria-labelledby="concept-heading">
          <span className="eyebrow">Your toolkit</span>
          <h2 id="concept-heading" className="mt-4 text-2xl font-semibold tracking-tight text-white">Concept progress</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">Each submission counts once per tagged concept. Browser practice counts a full pass when all visible tests pass; it does not check hidden tests. Different passing solutions count once each, even if you submit the same code again.</p>
          <div className="mt-5 rounded-2xl border border-white/10 bg-[#10151d] p-5 text-xs leading-6 text-slate-300 sm:text-sm">
            <p><strong className="text-white">Not started:</strong> no attempts. <strong className="text-white">Practicing:</strong> attempts without a sustained pass pattern.</p>
            <p><strong className="text-white">Improving:</strong> at least two attempts and a full pass on the latest attempt. <strong className="text-white">Demonstrated:</strong> at least three attempts, two different passing solutions, and two full passes among the latest three attempts.</p>
          </div>
          {progress.concepts.length ? <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{progress.concepts.map((item) => <article key={item.concept} className="panel p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="flex items-center gap-2 text-lg font-semibold text-white"><QuestIcon name={conceptIcons[item.concept] ?? "layers"} className="h-5 w-5 text-lime-300" />{formatConcept(item.concept)}</h3><span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold capitalize ${statusStyle[item.status]}`}><QuestIcon name={statusIcons[item.status]} className="h-3.5 w-3.5" />{item.status}</span></div>
            <p className="mt-4 text-sm text-slate-300"><strong className="text-white">{item.passed_attempts}</strong> full passes in <strong className="text-white">{item.attempts}</strong> attempts</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">{item.distinct_passing_solutions} different passing solutions · {item.completed_challenges} of {item.available_challenges} challenges complete</p>
            <div className="mt-4 border-t border-white/10 pt-4"><p className="text-xs font-bold uppercase tracking-[.12em] text-slate-500">Latest attempts · newest first</p><div className="mt-2 flex flex-wrap gap-2">{item.recent_results.length ? item.recent_results.map((result, index) => <span key={index} className={`rounded-md px-2 py-1 text-xs font-semibold capitalize ${result === "passed" ? "bg-emerald-300/10 text-emerald-200" : "bg-white/[0.055] text-slate-300"}`}>{result}</span>) : <span className="text-xs text-slate-500">No attempts yet</span>}</div></div>
          </article>)}</div> : <p className="mt-6 text-sm text-slate-400">Concepts will appear when challenges are available.</p>}
        </section>
      </> : null}
    </main>
  );
}
