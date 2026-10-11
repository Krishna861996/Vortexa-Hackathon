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
  const milestones = [
    { name: "First steps", text: "Complete your first challenge", icon: "flag" as const, earned: solved.size >= 1 },
    { name: "Keep exploring", text: "Practice three concepts", icon: "compass" as const, earned: (progress?.concepts_practiced.length ?? 0) >= 3 },
    { name: "Skill demonstrated", text: "Demonstrate one concept", icon: "medal" as const, earned: progress?.concepts.some((item) => item.status === "demonstrated") ?? false },
  ];

  return <main className="quest-container">
    <section className="quest-hero" data-reveal>
      <div className="hero-copy"><div className="hero-kicker"><span className="status-dot" /> A little practice goes a long way</div>
        <h1>Small challenges.<br /><span className="hero-blue">Big possibilities.</span></h1>
        <p>An intelligent Python learning mentor built for beginners, students, and self-taught coders. CodeQuest AI breaks programming into bite-sized challenges, tests your solutions in real time, and provides progressive hints so you never get stuck.</p>
        <div className="hero-actions"><a href="#challenges" className="primary-button">{next ? "Continue your quest" : "Explore challenges"}<QuestIcon name="arrow" /></a><span className="hero-note">One function. One step forward.</span></div>
      </div>
      <div className="hero-emblem"><div className="emblem-orbit"><PythonMark className="h-24 w-24 sm:h-28 sm:w-28" /></div><span className="emblem-label">PYTHON / YOUR PACE</span></div>
    </section>

    <div className="quest-workspace">
      <section id="challenges" className="quest-library">
        <div className="library-heading" data-reveal><div><span className="eyebrow">The practice path</span><h2>Your next small win.</h2><p className="unlock-help">Finish each level to open the next. Beginner → Easy → Medium → Hard → Advanced.</p></div><span className="library-count">{status === "ready" ? filtered.length + " challenges" : "Loading…"}</span></div>
        {status === "ready" && challenges.length > 0 ? <div className="filter-bar" data-reveal><div className="level-filters" role="group" aria-label="Difficulty"><button onClick={() => setDifficulty("all")} aria-pressed={difficulty === "all"} className={difficulty === "all" ? "filter-active" : ""}>All levels</button>{DIFFICULTY_ORDER.map((level) => <button key={level} onClick={() => setDifficulty(level)} aria-pressed={difficulty === level} className={difficulty === level ? "filter-active" : ""}><QuestIcon name={difficultyIcons[level]} className="h-4 w-4" />{level}</button>)}</div><label className="concept-filter"><span className="sr-only">Filter by concept</span><select value={concept} onChange={(event) => setConcept(event.target.value)}><option value="all">All concepts</option>{concepts.map((item) => <option key={item} value={item}>{formatConcept(item)}</option>)}</select></label></div> : null}
        <div className="quest-trail">
          {status === "loading" ? [1, 2, 3].map((item) => <div key={item} className="skeleton mb-5 h-36 rounded-xl" />) : null}
          {status === "error" ? <StatusState tone="error" title="Challenges could not load" description={error} action={<button className="secondary-button" onClick={() => { setStatus("loading"); setRefreshKey((key) => key + 1); }}>Try again</button>} /> : null}
          {status === "ready" && !filtered.length ? <StatusState title={challenges.length ? "No matches yet" : "Your path is being prepared"} description={challenges.length ? "Choose another level or concept to find a challenge." : "No challenges are available yet."} action={<button className="secondary-button" onClick={() => { setDifficulty("all"); setConcept("all"); }}>Clear filters</button>} /> : null}
          {status === "ready" ? filtered.map((item) => {
            const complete = solved.has(item.id); const current = next?.id === item.id;
            return <div className={"trail-step " + (complete ? "trail-complete " : "") + (current ? "trail-current" : "")} key={item.id} data-reveal>
              <span className="trail-node" aria-hidden="true">{complete ? <QuestIcon name="check" className="h-4 w-4" /> : <span />}</span>
              <Link href={item.locked ? "#challenges" : "/challenges/" + item.id} aria-disabled={item.locked} onClick={(event) => { if (item.locked) event.preventDefault(); }} className={"quest-card panel " + (item.locked ? "quest-card-locked" : current ? "quest-card-current" : "")}>
                <div className="quest-card-top"><span className="question-icon"><QuestIcon name={challengeIcons[item.id] ?? "terminal"} className="h-6 w-6" /></span><span className={"difficulty-badge difficulty-" + item.difficulty}><QuestIcon name={difficultyIcons[item.difficulty]} className="h-3.5 w-3.5" />{item.difficulty}</span></div>
                <div className="quest-card-body"><div><span className="quest-number">QUEST {String(ordered.findIndex((challenge) => challenge.id === item.id) + 1).padStart(2, "0")}{complete ? " / COMPLETE" : current ? " / UP NEXT" : ""}</span><h3>{item.title}</h3><div className="quest-concepts">{item.concept_tags.map((tag) => <span key={tag}>{formatConcept(tag)}</span>)}</div>{item.recommended_reason ? <p className="mt-2 text-xs font-medium text-amber-300">★ {item.recommended_reason}</p> : null}</div><span className="card-arrow"><QuestIcon name={item.locked ? "lock" : "arrow"} /></span></div>
                {item.locked ? <p className="lock-explanation">{item.unlock_message}</p> : null}
              </Link>
            </div>;
          }) : null}
        </div>
        <div className="path-footer" data-reveal><QuestIcon name="terminal" /><p>No rush. Every line is a little more understanding.</p></div>
      </section>

      <aside className="quest-sidebar">
        <section className="panel progress-overview"><div className="sidebar-heading"><h2>Your progress</h2><QuestIcon name="layers" /></div>
          <div className="progress-ring"><svg viewBox="0 0 160 160" aria-hidden="true"><circle cx="80" cy="80" r="65" className="ring-track" /><circle cx="80" cy="80" r="65" className="ring-fill" strokeDasharray="408.4" strokeDashoffset={408.4 * (1 - percentage / 100)} /></svg><div><strong>{progress ? solved.size + "/" + challenges.length : "—"}</strong><span>completed</span></div></div>
          {progressError ? <p className="sidebar-note">Progress couldn’t load. <Link href="/progress">Try again</Link></p> : <p className="sidebar-note">{solved.size ? "Look how far you’ve come." : "Your first win starts with one try."}</p>}
          <div className="sidebar-stats"><div><strong>{progress?.total_attempts ?? "—"}</strong><span>code runs</span></div><div><strong>{progress?.concepts_practiced.length ?? "—"}</strong><span>concepts explored</span></div></div>
          <Link href={user ? "/progress" : "/login"} className="sidebar-link">{user ? "See your journey" : "Log in to save your progress"}<QuestIcon name="arrow" className="h-4 w-4" /></Link>
        </section>
        <section className="panel milestone-panel"><div className="sidebar-heading"><h2>Little milestones</h2><span className="yellow-dot" /></div><p className="sidebar-note">Small wins worth noticing.</p><div className="milestone-list">{milestones.map((item) => <div key={item.name} className={"milestone " + (item.earned ? "milestone-earned" : "")}><span className="milestone-icon"><QuestIcon name={item.icon} className="h-5 w-5" /></span><div><h3>{item.name}{item.earned ? <span className="sr-only"> — achieved</span> : null}</h3><p>{item.text}</p></div>{item.earned ? <QuestIcon name="check" className="h-4 w-4 text-[#ffd343]" /> : null}</div>)}</div><p className="milestone-footnote">Based on saved practice results from visible browser tests.</p></section>
        <div className="practice-note" data-reveal><span>01 / READ. WRITE. REPEAT.</span><p>You don’t need to know<br />everything to begin.</p><span className="note-rule" /></div>
      </aside>
    </div>
  </main>;
}
