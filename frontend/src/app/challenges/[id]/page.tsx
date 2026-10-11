"use client";

import Link from "next/link";
import { RequireLogin } from "@/components/AuthProvider";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { QuestIcon, difficultyIcons } from "@/components/QuestIcon";
import { SolvedCelebration } from "@/components/SolvedCelebration";
import { ResultsPanel } from "@/components/ResultsPanel";
import { CodeDiffReview } from "@/components/CodeDiffReview";
import { StatusState } from "@/components/StatusState";
import { api, formatConcept, type AttemptResponse, type ChallengeDetail, type StoredAttempt } from "@/lib/api";
import { runVisibleTests } from "@/lib/pyodide";

type LoadState = "loading" | "ready" | "error";
type RevealedHint = { number: number; text: string };

function cleanStarterCode(code: string): string {
  const lines = code.split("\n").filter((line) => {
    const trimmed = line.trim();
    return !trimmed.startsWith("#") && trimmed !== "count = 0" && trimmed !== "total = 0";
  });
  const cleaned = lines.join("\n").trim();
  return cleaned.endsWith("pass") || cleaned.includes("return") ? cleaned : `${cleaned}\n    pass`;
}

export default function ChallengePage() {
  return <RequireLogin><ChallengeContent /></RequireLogin>;
}

function ChallengeContent() {
  const { id } = useParams<{ id: string }>();
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [running, setRunning] = useState(false);
  const [attempt, setAttempt] = useState<AttemptResponse | null>(null);
  const [pastAttempts, setPastAttempts] = useState<StoredAttempt[]>([]);
  const [runError, setRunError] = useState("");
  const [celebrating, setCelebrating] = useState(false);
  const [nextChallenge, setNextChallenge] = useState<{ id: string; title: string } | null>(null);
  const [hints, setHints] = useState<RevealedHint[]>([]);
  const [hintError, setHintError] = useState("");
  const [hintLoading, setHintLoading] = useState(false);
  const [hintsExhausted, setHintsExhausted] = useState(false);
  const [mentorQuestion, setMentorQuestion] = useState("");
  const [mentorAnswer, setMentorAnswer] = useState<{ answer: string; source: "gemini" | "local" } | null>(null);
  const [mentorLoading, setMentorLoading] = useState(false);
  const [mentorError, setMentorError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    api.getChallenge(id, controller.signal)
      .then((item) => {
        setChallenge(item);
        setCode(cleanStarterCode(item.starter_code));
        setAttempt(null);
        setCelebrating(false);
        setNextChallenge(null);
        setHints([]);
        setHintsExhausted(item.hint_count === 0);
        setMentorAnswer(null);
        setStatus("ready");
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setLoadError(reason instanceof Error ? reason.message : "Could not load this challenge.");
        setStatus("error");
      });

    api.getChallengeAttempts(id, controller.signal)
      .then((items) => setPastAttempts(items))
      .catch(() => {});

    return () => controller.abort();
  }, [id, refreshKey]);

  async function runCode() {
    if (!challenge || challenge.locked || !code.trim() || running) return;
    setRunning(true);
    setCelebrating(false);
    setRunError("");
    setAttempt(null);
    try {
      const results = await runVisibleTests(challenge, code);
      const saved = await api.savePractice(challenge.id, code, results);
      setAttempt(saved);
      setPastAttempts((prev) => [
        {
          id: saved.id,
          challenge_id: challenge.id,
          submitted_code: code,
          test_results: results,
          passed: saved.passed,
          submitted_at: saved.submitted_at,
        },
        ...prev,
      ]);
      if (saved.passed) {
        setCelebrating(true);
        const [library, progress] = await Promise.all([api.listChallenges(), api.getProgress()]).catch(() => [[], null] as const);
        const completed = new Set(progress?.challenges.filter((item) => item.solved).map((item) => item.challenge_id) ?? []);
        setNextChallenge(library.find((item) => !item.locked && item.id !== challenge.id && !completed.has(item.id)) ?? null);
      }
    } catch (reason) {
      setRunError(reason instanceof Error ? reason.message : "Could not run your code.");
    } finally {
      setRunning(false);
    }
  }

  async function askMentor(mode: "guidance" | "deep_hint" = "guidance") {
    if (!challenge || mentorLoading) return;
    const promptText = mode === "deep_hint"
      ? "Please provide a more specific progressive hint for the trickiest part of this challenge."
      : mentorQuestion;
    if (mode === "guidance" && !mentorQuestion.trim()) return;
    setMentorLoading(true); setMentorError("");
    try {
      setMentorAnswer(await api.mentor(challenge.id, code, promptText, mode));
      if (mode === "guidance") setMentorQuestion("");
    } catch (reason) {
      setMentorError(reason instanceof Error ? reason.message : "Could not reach the mentor.");
    } finally {
      setMentorLoading(false);
    }
  }

  async function requestHint() {
    if (!challenge || hintLoading || hintsExhausted) return;
    setHintLoading(true);
    setHintError("");
    try {
      const response = await api.nextHint(challenge.id, hints.length);
      const hint = response.hint;
      if (hint !== null) setHints((current) => [...current, { number: response.hint_number, text: hint }]);
      setHintsExhausted(hint !== null && response.exhausted && hints.length + 1 >= challenge.hint_count);
    } catch (reason) {
      setHintError(reason instanceof Error ? reason.message : "Could not load a hint.");
    } finally {
      setHintLoading(false);
    }
  }

  function retryInEditor() {
    editorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    editorRef.current?.focus({ preventScroll: true });
  }

  function handleEditorKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Tab") return;
    event.preventDefault();
    const editor = event.currentTarget;
    const { selectionStart, selectionEnd } = editor;
    setCode((current) => `${current.slice(0, selectionStart)}    ${current.slice(selectionEnd)}`);
    requestAnimationFrame(() => editorRef.current?.setSelectionRange(selectionStart + 4, selectionStart + 4));
  }

  return (
    <main className="mx-auto w-full max-w-7xl px-5 pb-20 pt-8 sm:px-8 lg:px-10">
      <Link href="/" className="inline-flex min-h-10 items-center gap-2 text-sm font-semibold text-slate-400 hover:text-lime-300"><span aria-hidden="true">←</span> All missions</Link>
      {status === "loading" ? <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(360px,.9fr)]"><div className="skeleton h-105 rounded-2xl" /><div className="skeleton h-105 rounded-2xl" /></div> : null}
      {status === "error" ? <div className="mt-7"><StatusState tone="error" title="Mission could not load" description={loadError} action={<button type="button" className="secondary-button" onClick={() => { setStatus("loading"); setRefreshKey((key) => key + 1); }}>Try again</button>} /></div> : null}
      {status === "ready" && challenge?.locked ? <div className="mt-7"><StatusState title="This mission is locked" description={challenge.unlock_message ?? "Complete the previous level first."} action={<Link className="primary-button" href="/">Back to your path</Link>} /></div> : null}
      {status === "ready" && challenge && !challenge.locked ? <>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <span className={`difficulty-badge difficulty-${challenge.difficulty}`}>
            <QuestIcon name={difficultyIcons[challenge.difficulty]} className="h-4 w-4" />{challenge.difficulty}
          </span>
          <span className="rounded-md bg-lime-400/15 px-2.5 py-0.5 text-xs font-mono font-bold text-lime-300">
            +{challenge.xp_value ?? 100} Base XP
          </span>
          <span className="rounded-md bg-amber-400/15 px-2.5 py-0.5 text-xs font-bold text-amber-300">
            +50 Solo Bonus XP (0 hints)
          </span>
          {challenge.is_daily ? (
            <span className="rounded-md bg-sky-400/20 px-2.5 py-0.5 text-xs font-bold text-sky-300">
              🎯 Featured Daily Mission
            </span>
          ) : null}
        </div>
        
        <div className="mt-4 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <span className="eyebrow text-lime-300">
              MISSION {String(challenge.mission_number ?? 1).padStart(2, "0")}
            </span>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              {challenge.mission_title ?? challenge.title}
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
              Inspect the challenge, write your clean solution, and pass the tests. Solve solo without hints to maximize your XP reward!
            </p>
          </div>
          <Link href="/progress" className="text-sm font-semibold text-lime-300 hover:text-lime-200">
            View rank & badges <span aria-hidden="true">↗</span>
          </Link>
        </div>

        {/* Mission Objectives Card */}
        <section className="mt-6 rounded-xl border border-white/10 bg-[#0c121b] p-4 text-xs sm:text-sm">
          <div className="flex items-center justify-between border-b border-white/5 pb-2 font-semibold text-slate-300">
            <span>🎯 Mission Objectives</span>
            <span className="text-xs text-lime-300">Independent Solvers earn 3 Stars ⭐⭐⭐</span>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-5 text-slate-400">
            <div className="flex items-center gap-1.5"><span className="text-lime-400">1.</span> Find mistake / inspect prompt</div>
            <div className="flex items-center gap-1.5"><span className="text-amber-400">2.</span> Request hints only if stuck</div>
            <div className="flex items-center gap-1.5"><span className="text-sky-400">3.</span> Correct the code</div>
            <div className="flex items-center gap-1.5"><span className="text-emerald-400">4.</span> Pass all tests</div>
            <div className="flex items-center gap-1.5"><span className="text-purple-400">5.</span> Unlock next mission</div>
          </div>
        </section>

        <div className="mt-8 grid items-start gap-6 lg:grid-cols-[minmax(0,.86fr)_minmax(0,1.14fr)]">
          <div className="space-y-6">
            <section className="panel p-6 sm:p-7" aria-labelledby="task-heading">
              <span className="eyebrow">The task</span><h2 id="task-heading" className="mt-4 text-xl font-semibold text-white">What you need to build</h2>
              <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-300">{challenge.description}</p>
              <div className="mt-6 flex flex-wrap gap-2">{challenge.concept_tags.map((tag) => <span key={tag} className="tag">{formatConcept(tag)}</span>)}</div>
            </section>
            <section className="panel p-6 sm:p-7" aria-labelledby="examples-heading">
              <div className="flex items-center justify-between gap-3"><div><span className="eyebrow">Examples</span><h2 id="examples-heading" className="mt-4 text-xl font-semibold text-white">Visible tests</h2></div><span className="text-xs text-slate-500">{challenge.visible_tests.length} shown</span></div>
              {challenge.visible_tests.length ? <div className="mt-5 space-y-3">{challenge.visible_tests.map((test, index) => <div key={index} className="rounded-xl border border-white/10 bg-[#0c121b] p-4 font-mono text-xs leading-6 sm:text-sm"><div className="flex flex-wrap gap-2"><span className="text-slate-500">Input</span><code className="break-all text-slate-200">{challenge.function_name}({test.input.map((value) => JSON.stringify(value)).join(", ")})</code></div><div className="mt-1 flex flex-wrap gap-2"><span className="text-slate-500">Expected</span><code className="break-all text-lime-200">{JSON.stringify(test.expected)}</code></div></div>)}</div> : <p className="mt-4 text-sm text-slate-400">No visible examples are available for this challenge.</p>}
              <p className="mt-5 text-xs leading-5 text-slate-500">Browser practice checks these visible examples. Hidden tests stay on the server.</p>
            </section>
            {challenge.hint_count > 0 ? (
              <section className="panel p-6 sm:p-7" aria-labelledby="hints-heading">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <span className="eyebrow">Need a nudge?</span>
                    <h2 id="hints-heading" className="mt-4 text-xl font-semibold text-white">Progressive Hints</h2>
                  </div>
                  <span className="text-xs text-slate-500">{challenge.hint_count} available</span>
                </div>
                <div className="mt-2 rounded-lg border border-amber-400/20 bg-amber-400/[0.06] p-3 text-xs leading-5 text-amber-200">
                  ⚡ <strong>Unique twist:</strong> Solved with 0 hints awards <strong>+50 Solo Maverick Bonus XP</strong> and 3 stars! Each hint revealed slightly scales down XP points.
                </div>
                <div className="mt-4 space-y-3" aria-live="polite">
                  {hints.map((hint) => (
                    <p key={hint.number} className="rounded-xl border border-lime-300/15 bg-lime-300/[0.055] p-4 text-sm leading-6 text-lime-100">
                      <span className="mr-2 font-bold text-lime-300">Hint {hint.number} of {challenge.hint_count}.</span>{hint.text}
                    </p>
                  ))}
                </div>
                {hintError ? <p role="alert" className="mt-3 text-sm text-rose-300">{hintError}</p> : null}
                <div className="mt-5 flex flex-wrap gap-3">
                  <button type="button" className="secondary-button" onClick={requestHint} disabled={hintLoading || hintsExhausted}>
                    {hintLoading ? "Loading hint…" : hintsExhausted ? "No more hints" : "Show next hint (-XP penalty)"}
                  </button>
                  {hints.length > 0 ? (
                    <button type="button" className="primary-button" onClick={retryInEditor}>
                      Try in my code <span aria-hidden="true">→</span>
                    </button>
                  ) : null}
                </div>
              </section>
            ) : null}
            {hintsExhausted ? <section className="panel p-6 sm:p-7" aria-labelledby="mentor-heading"><span className="eyebrow">Still stuck?</span><h2 id="mentor-heading" className="mt-4 text-xl font-semibold text-white">Ask the coding mentor</h2><p className="mt-3 text-sm leading-6 text-slate-400">All challenge hints are unlocked. Get progressive hints that guide your logic step-by-step without revealing the full solution.</p>{mentorAnswer ? <div className="mt-4 rounded-xl border border-cyan-300/15 bg-cyan-300/[0.05] p-4 text-sm leading-6 text-cyan-50"><p className="mb-2 text-xs font-bold uppercase tracking-[.12em] text-cyan-300">{mentorAnswer.source === "gemini" ? "Gemini mentor" : "Local mentor"}</p><div className="whitespace-pre-wrap font-mono">{mentorAnswer.answer}</div></div> : null}<label htmlFor="mentor-question" className="mt-4 block text-xs text-slate-400">Your question</label><textarea id="mentor-question" maxLength={1000} value={mentorQuestion} onChange={(event) => setMentorQuestion(event.target.value)} className="mt-4 min-h-24 w-full rounded-xl border border-white/10 bg-[#0c121b] p-3 text-sm text-slate-100 outline-none focus:border-cyan-300/60" placeholder="What part is confusing?" /><div className="mt-3 flex flex-wrap gap-3"><button type="button" className="secondary-button" onClick={() => askMentor()} disabled={mentorLoading || !mentorQuestion.trim()}>{mentorLoading ? "Thinking…" : "Ask mentor"}</button><button type="button" className="secondary-button" onClick={() => askMentor("deep_hint")} disabled={mentorLoading}>Get deeper hint</button></div>{mentorError ? <p role="alert" className="mt-3 text-sm text-rose-300">{mentorError}</p> : null}</section> : null}
          </div>
          <div className="space-y-6 lg:sticky lg:top-6">
            <section className="panel overflow-hidden" aria-labelledby="editor-heading">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-4 sm:px-6"><div><p className="text-[11px] font-bold uppercase tracking-[.16em] text-slate-500">Workspace</p><h2 id="editor-heading" className="mt-1 text-lg font-semibold text-white">Your Python code</h2></div><span className="rounded-lg bg-[#172c43] px-2.5 py-1.5 font-mono text-xs text-lime-200">solution.py</span></div>
              <div className="bg-[#090e15] p-4 sm:p-5"><label htmlFor="python-editor" className="sr-only">Python solution</label><textarea id="python-editor" ref={editorRef} value={code} onChange={(event) => setCode(event.target.value)} onKeyDown={handleEditorKeyDown} spellCheck={false} autoCapitalize="off" autoCorrect="off" className="block min-h-88 w-full resize-y rounded-lg border border-white/10 bg-[#0c121b] p-4 font-mono text-[13px] leading-7 text-slate-100 outline-none placeholder:text-slate-600 focus:border-lime-300/60 sm:min-h-105 sm:text-sm" placeholder="Enter your code here" /></div>
              <div className="flex flex-col gap-4 border-t border-white/10 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6"><p className="text-xs leading-5 text-slate-500">Keep the function name and parameters from the starter code.</p><button type="button" className="primary-button shrink-0" onClick={runCode} disabled={running || !code.trim()}>{running ? "Running tests…" : "Run code"}<span aria-hidden="true"><QuestIcon name="terminal" className="h-4 w-4" /></span></button></div>
            </section>
            {celebrating ? (
              <SolvedCelebration
                next={nextChallenge}
                onClose={() => setCelebrating(false)}
                earnedXp={attempt?.earned_xp}
                soloBonus={attempt?.solo_bonus}
                stars={attempt?.stars}
                levelName={attempt?.level_name}
              />
            ) : null}
            <ResultsPanel attempt={attempt} running={running} error={runError} onRetry={retryInEditor} />
            <CodeDiffReview
              challengeId={challenge.id}
              currentCode={code}
              attempts={pastAttempts}
              onRestoreCode={(restoredCode) => {
                setCode(restoredCode);
                retryInEditor();
              }}
            />
          </div>
        </div>
      </> : null}
    </main>
  );
}
