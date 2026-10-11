"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusState } from "@/components/StatusState";
import { useAuth } from "@/components/AuthProvider";
import { QuestIcon, PythonMark, challengeIcons, difficultyIcons } from "@/components/QuestIcon";
import { api, DIFFICULTY_ORDER, formatConcept, type ChallengeSummary, type Difficulty, type LearnerProgress } from "@/lib/api";

export default function HomePage() {
  const { user } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeSummary[]>([]);
  const [progress, setProgress] = useState<LearnerProgress | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");
  const [progressError, setProgressError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [difficulty, setDifficulty] = useState<Difficulty | "all">("all");
  const [concept, setConcept] = useState("all");
  const [viewMode, setViewMode] = useState<"trail" | "map">("trail");

  useEffect(() => {
    const controller = new AbortController();
    api.listChallenges(controller.signal).then((items) => { setChallenges(items); setStatus("ready"); }).catch((reason: unknown) => {
      if (controller.signal.aborted) return;
      setError(reason instanceof Error ? reason.message : "Could not load challenges."); setStatus("error");
    });
    if (user) api.getProgress(controller.signal).then((item) => { setProgress(item); setProgressError(false); }).catch(() => { if (!controller.signal.aborted) setProgressError(true); });
    return () => controller.abort();
  }, [refreshKey, user]);

  const ordered = [...challenges].sort((a, b) => DIFFICULTY_ORDER.indexOf(a.difficulty) - DIFFICULTY_ORDER.indexOf(b.difficulty));
  const concepts = Array.from(new Set(challenges.flatMap((item) => item.concept_tags))).sort();
  const filtered = ordered.filter((item) => (difficulty === "all" || item.difficulty === difficulty) && (concept === "all" || item.concept_tags.includes(concept)));
  const solved = new Set(progress?.challenges.filter((item) => item.solved).map((item) => item.challenge_id) ?? []);
  const next = ordered.find((item) => !item.locked && !solved.has(item.id));
  const percentage = challenges.length ? Math.min(100, Math.round(solved.size / challenges.length * 100)) : 0;

  const dailyId = progress?.daily_challenge_id || challenges.find((c) => c.is_daily)?.id;
  const dailyChallenge = challenges.find((c) => c.id === dailyId);
  const dailyCompleted = progress?.daily_challenge_completed || (dailyId ? solved.has(dailyId) : false);

  const starMap: Record<string, number> = {};
  if (progress?.progress_map) {
    for (const node of progress.progress_map) {
      if (node.stars > 0) starMap[node.challenge_id] = node.stars;
    }
  }

  const milestones = [
    { name: "First steps", text: "Complete your first mission", icon: "flag" as const, earned: solved.size >= 1 },
    { name: "Solo Maverick", text: "Solve with 0 hints (+50 Solo XP)", icon: "medal" as const, earned: (progress?.badges?.some((b) => b.id === "solo_maverick" && b.unlocked) ?? false) },
    { name: "Skill demonstrated", text: "Demonstrate one concept", icon: "mountain" as const, earned: progress?.concepts.some((item) => item.status === "demonstrated") ?? false },
  ];

  return <main className="quest-container">
    <section className="quest-hero" data-reveal>
      <div className="hero-copy"><div className="hero-kicker"><span className="status-dot" /> A little practice goes a long way</div>
        <h1>Small challenges.<br /><span className="hero-blue">Big possibilities.</span></h1>
        <p>An intelligent Python learning mentor built for beginners, students, and self-taught coders. CodeQuest AI breaks programming into bite-sized missions, tests your solutions in real time, and provides progressive hints with XP bonuses for independent solving.</p>
        <div className="hero-actions">
          <a href="#challenges" className="primary-button">{next ? "Continue your quest" : "Explore challenges"}<QuestIcon name="arrow" /></a>
          <span className="hero-note">One mission. One step forward.</span>
        </div>
      </div>
      <div className="hero-emblem"><div className="emblem-orbit"><PythonMark className="h-24 w-24 sm:h-28 sm:w-28" /></div><span className="emblem-label">PYTHON / YOUR PACE</span></div>
    </section>

    {/* Daily Challenge Banner */}
    {dailyChallenge ? (
      <section className="mb-8 rounded-2xl border border-amber-400/25 bg-gradient-to-r from-amber-500/10 via-[#0c121b] to-amber-500/5 p-5 shadow-lg backdrop-blur-sm sm:p-6" data-reveal>
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-400/20 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-amber-300">
                🎯 Featured Daily Mission
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-sky-400/20 px-2.5 py-1 text-xs font-bold text-sky-300">
                +50 Daily Bonus XP
              </span>
              {progress?.daily_streak ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-orange-400/20 px-2.5 py-1 text-xs font-bold text-orange-300">
                  🔥 {progress.daily_streak} Day Streak
                </span>
              ) : null}
            </div>
            <h3 className="text-xl font-bold text-white sm:text-2xl">
              {dailyChallenge.mission_title ?? dailyChallenge.title}
            </h3>
            <p className="text-xs text-slate-300 sm:text-sm">
              Complete today’s mission to keep your learning streak alive and boost your XP rank.
            </p>
          </div>
          <Link
            href={`/challenges/${dailyChallenge.id}`}
            className="flex-none rounded-xl border border-amber-400/30 bg-amber-400/15 px-5 py-3 text-sm font-bold text-amber-200 transition-all hover:bg-amber-400/25 hover:text-white"
          >
            {dailyCompleted ? "Mission Completed ✓" : "Accept Daily Mission →"}
          </Link>
        </div>
      </section>
    ) : null}

    <div className="quest-workspace">
      <section id="challenges" className="quest-library">
        <div className="library-heading" data-reveal>
          <div>
            <span className="eyebrow">The practice path</span>
            <h2>Your next small win.</h2>
            <p className="unlock-help">Finish each level to open the next. Beginner → Easy → Medium → Hard → Advanced.</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="inline-flex rounded-lg border border-white/10 bg-white/5 p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setViewMode("trail")}
                className={`rounded-md px-3 py-1 font-semibold transition-all ${viewMode === "trail" ? "bg-lime-400/20 text-lime-300" : "text-slate-400 hover:text-white"}`}
              >
                Missions
              </button>
              <button
                type="button"
                onClick={() => setViewMode("map")}
                className={`rounded-md px-3 py-1 font-semibold transition-all ${viewMode === "map" ? "bg-lime-400/20 text-lime-300" : "text-slate-400 hover:text-white"}`}
              >
                Progress Map
              </button>
            </div>
            <span className="library-count">{status === "ready" ? filtered.length + " missions" : "Loading…"}</span>
          </div>
        </div>

        {status === "ready" && challenges.length > 0 ? (
          <div className="filter-bar" data-reveal>
            <div className="level-filters" role="group" aria-label="Difficulty">
              <button onClick={() => setDifficulty("all")} aria-pressed={difficulty === "all"} className={difficulty === "all" ? "filter-active" : ""}>All levels</button>
              {DIFFICULTY_ORDER.map((level) => (
                <button key={level} onClick={() => setDifficulty(level)} aria-pressed={difficulty === level} className={difficulty === level ? "filter-active" : ""}>
                  <QuestIcon name={difficultyIcons[level]} className="h-4 w-4" />{level}
                </button>
              ))}
            </div>
            <label className="concept-filter">
              <span className="sr-only">Filter by concept</span>
              <select value={concept} onChange={(event) => setConcept(event.target.value)}>
                <option value="all">All concepts</option>
                {concepts.map((item) => <option key={item} value={item}>{formatConcept(item)}</option>)}
              </select>
            </label>
          </div>
        ) : null}

        {viewMode === "map" ? (
          /* Progress Map View */
          <div className="rounded-2xl border border-white/10 bg-[#0c121b] p-6" data-reveal>
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white">Python Mission Roadmap</h3>
                <p className="text-xs text-slate-400">Step through each mission node. Earn 3 stars by solving without hints!</p>
              </div>
              <span className="rounded-full bg-lime-300/15 px-3 py-1 text-xs font-bold text-lime-300">
                {solved.size} / {challenges.length} Conquered
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {ordered.map((item, idx) => {
                const complete = solved.has(item.id);
                const current = next?.id === item.id;
                const stars = starMap[item.id] ?? (item.stars ?? 0);
                const missionTitle = item.mission_title ?? `Mission ${String(idx + 1).padStart(2, "0")}: ${item.title}`;

                return (
                  <Link
                    key={item.id}
                    href={item.locked ? "#challenges" : `/challenges/${item.id}`}
                    onClick={(e) => { if (item.locked) e.preventDefault(); }}
                    className={`flex flex-col justify-between rounded-xl border p-4 transition-all ${
                      item.locked
                        ? "cursor-not-allowed border-white/5 bg-white/[0.02] opacity-60"
                        : current
                        ? "border-lime-300/50 bg-lime-400/10 shadow-[0_0_15px_rgba(163,230,53,0.15)]"
                        : complete
                        ? "border-emerald-500/30 bg-emerald-500/[0.06]"
                        : "border-white/10 bg-white/[0.04] hover:border-white/20"
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between text-xs font-bold">
                        <span className="text-slate-400">NODE {String(idx + 1).padStart(2, "0")}</span>
                        <span className={`capitalize ${item.difficulty === "beginner" ? "text-emerald-300" : item.difficulty === "easy" ? "text-sky-300" : item.difficulty === "medium" ? "text-amber-300" : "text-rose-300"}`}>
                          {item.difficulty}
                        </span>
                      </div>
                      <h4 className="mt-2 font-bold text-white">{missionTitle}</h4>
                    </div>
                    <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-xs">
                      <div className="flex items-center gap-1 text-amber-300">
                        {complete ? (
                          <>
                            {"★".repeat(stars || 3)}
                            {"☆".repeat(Math.max(0, 3 - (stars || 3)))}
                          </>
                        ) : (
                          <span className="text-slate-500">Unsolved</span>
                        )}
                      </div>
                      <span className="font-mono text-lime-300">+{item.xp_value ?? 100} XP</span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ) : (
          /* Classic Trail View */
          <div className="quest-trail">
            {status === "loading" ? [1, 2, 3].map((item) => <div key={item} className="skeleton mb-5 h-36 rounded-xl" />) : null}
            {status === "error" ? <StatusState tone="error" title="Challenges could not load" description={error} action={<button className="secondary-button" onClick={() => { setStatus("loading"); setRefreshKey((key) => key + 1); }}>Try again</button>} /> : null}
            {status === "ready" && !filtered.length ? <StatusState title={challenges.length ? "No matches yet" : "Your path is being prepared"} description={challenges.length ? "Choose another level or concept to find a challenge." : "No challenges are available yet."} action={<button className="secondary-button" onClick={() => { setDifficulty("all"); setConcept("all"); }}>Clear filters</button>} /> : null}
            {status === "ready" ? filtered.map((item) => {
              const complete = solved.has(item.id);
              const current = next?.id === item.id;
              const stars = starMap[item.id] ?? (item.stars ?? 0);
              const missionTitle = item.mission_title ?? `Mission ${String(ordered.findIndex((c) => c.id === item.id) + 1).padStart(2, "0")}: ${item.title}`;

              return <div className={"trail-step " + (complete ? "trail-complete " : "") + (current ? "trail-current" : "")} key={item.id} data-reveal>
                <span className="trail-node" aria-hidden="true">{complete ? <QuestIcon name="check" className="h-4 w-4" /> : <span />}</span>
                <Link href={item.locked ? "#challenges" : "/challenges/" + item.id} aria-disabled={item.locked} onClick={(event) => { if (item.locked) event.preventDefault(); }} className={"quest-card panel " + (item.locked ? "quest-card-locked" : current ? "quest-card-current" : "")}>
                  <div className="quest-card-top">
                    <span className="question-icon"><QuestIcon name={challengeIcons[item.id] ?? "terminal"} className="h-6 w-6" /></span>
                    <div className="flex items-center gap-2">
                      {complete && stars > 0 ? (
                        <span className="rounded-md bg-amber-400/15 px-2 py-0.5 text-xs font-bold text-amber-300">
                          {"★".repeat(stars)}
                        </span>
                      ) : null}
                      <span className="rounded-md bg-lime-400/15 px-2 py-0.5 text-xs font-mono font-bold text-lime-300">
                        +{item.xp_value ?? 100} XP
                      </span>
                      <span className={"difficulty-badge difficulty-" + item.difficulty}><QuestIcon name={difficultyIcons[item.difficulty]} className="h-3.5 w-3.5" />{item.difficulty}</span>
                    </div>
                  </div>
                  <div className="quest-card-body">
                    <div>
                      <span className="quest-number">
                        MISSION {String(ordered.findIndex((challenge) => challenge.id === item.id) + 1).padStart(2, "0")}
                        {complete ? " / CONQUERED" : current ? " / UP NEXT" : ""}
                        {item.is_daily ? " / 🎯 DAILY" : ""}
                      </span>
                      <h3>{missionTitle}</h3>
                      <div className="quest-concepts">{item.concept_tags.map((tag) => <span key={tag}>{formatConcept(tag)}</span>)}</div>
                      {item.recommended_reason ? <p className="mt-2 text-xs font-medium text-amber-300">★ {item.recommended_reason}</p> : null}
                    </div>
                    <span className="card-arrow"><QuestIcon name={item.locked ? "lock" : "arrow"} /></span>
                  </div>
                  {item.locked ? <p className="lock-explanation">{item.unlock_message}</p> : null}
                </Link>
              </div>;
            }) : null}
          </div>
        )}

        <div className="path-footer" data-reveal><QuestIcon name="terminal" /><p>No rush. Every line is a little more understanding.</p></div>
      </section>

      <aside className="quest-sidebar">
        {/* XP & Level Panel */}
        <section className="panel progress-overview">
          <div className="sidebar-heading">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest text-lime-300">Player Rank</span>
              <h2 className="text-xl font-bold text-white">Level {progress?.current_level ?? 1}: {progress?.level_name ?? "Novice Coder"}</h2>
            </div>
            <span className="rounded-lg bg-lime-400/20 px-2.5 py-1 text-sm font-mono font-bold text-lime-300">
              {progress?.total_xp ?? 0} XP
            </span>
          </div>
          
          <div className="mt-4">
            <div className="flex justify-between text-xs font-medium text-slate-400">
              <span>Next Milestone</span>
              <span>{progress?.level_progress_pct ?? 0}%</span>
            </div>
            <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-gradient-to-r from-lime-400 to-emerald-400 transition-all duration-500"
                style={{ width: `${progress?.level_progress_pct ?? 0}%` }}
              />
            </div>
            <p className="mt-2 text-right text-[11px] text-slate-500">
              Target: {progress?.next_level_xp ?? 150} XP
            </p>
          </div>

          <div className="mt-5 border-t border-white/10 pt-4">
            <div className="progress-ring">
              <svg viewBox="0 0 160 160" aria-hidden="true">
                <circle cx="80" cy="80" r="65" className="ring-track" />
                <circle cx="80" cy="80" r="65" className="ring-fill" strokeDasharray="408.4" strokeDashoffset={408.4 * (1 - percentage / 100)} />
              </svg>
              <div>
                <strong>{progress ? solved.size + "/" + challenges.length : "—"}</strong>
                <span>completed</span>
              </div>
            </div>
          </div>

          <div className="sidebar-stats mt-4">
            <div><strong>{progress?.total_attempts ?? "—"}</strong><span>code runs</span></div>
            <div><strong>{progress?.daily_streak ?? 0}</strong><span>day streak 🔥</span></div>
          </div>
          <Link href={user ? "/progress" : "/login"} className="sidebar-link mt-4">{user ? "View Badges & Journey" : "Log in to save your progress"}<QuestIcon name="arrow" className="h-4 w-4" /></Link>
        </section>

        {/* Milestones Panel */}
        <section className="panel milestone-panel">
          <div className="sidebar-heading"><h2>Little milestones</h2><span className="yellow-dot" /></div>
          <p className="sidebar-note">Small wins worth noticing.</p>
          <div className="milestone-list">
            {milestones.map((item) => (
              <div key={item.name} className={"milestone " + (item.earned ? "milestone-earned" : "")}>
                <span className="milestone-icon"><QuestIcon name={item.icon} className="h-5 w-5" /></span>
                <div>
                  <h3>{item.name}{item.earned ? <span className="sr-only"> — achieved</span> : null}</h3>
                  <p>{item.text}</p>
                </div>
                {item.earned ? <QuestIcon name="check" className="h-4 w-4 text-[#ffd343]" /> : null}
              </div>
            ))}
          </div>
          <p className="milestone-footnote">Awarding extra XP for independent solving without hints!</p>
        </section>

        <div className="practice-note" data-reveal>
          <span>01 / READ. WRITE. REPEAT.</span>
          <p>You don’t need to know<br />everything to begin.</p>
          <span className="note-rule" />
        </div>
      </aside>
    </div>
  </main>;
}
