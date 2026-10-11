"use client";

import { useEffect, useState } from "react";
import { api, type DiffAnalysisResponse, type StoredAttempt } from "@/lib/api";

interface CodeDiffReviewProps {
  challengeId: string;
  currentCode: string;
  attempts: StoredAttempt[];
  onRestoreCode: (code: string) => void;
}

export function CodeDiffReview({
  challengeId,
  currentCode,
  attempts,
  onRestoreCode,
}: CodeDiffReviewProps) {
  const [selectedAttemptIndex, setSelectedAttemptIndex] = useState<number>(0);
  const [diffData, setDiffData] = useState<DiffAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedAttempt = attempts[selectedAttemptIndex] ?? null;
  const previousAttempt = attempts[selectedAttemptIndex + 1] ?? null;

  // Compare either selected attempt vs previous attempt, OR current editor code vs latest attempt
  const beforeCode = previousAttempt ? previousAttempt.submitted_code : selectedAttempt?.submitted_code ?? "";
  const afterCode = selectedAttempt ? selectedAttempt.submitted_code : currentCode;

  useEffect(() => {
    if (!beforeCode.trim() || !afterCode.trim()) {
      setDiffData(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError("");

    api
      .analyzeDiff(challengeId, beforeCode, afterCode)
      .then((data) => {
        if (active) setDiffData(data);
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : "Could not analyze diff.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [challengeId, beforeCode, afterCode]);

  if (attempts.length === 0) {
    return (
      <section className="panel p-6 sm:p-7" aria-labelledby="diff-heading">
        <div className="flex items-center justify-between">
          <span className="eyebrow text-sky-300">Code Evolution</span>
          <span className="text-xs text-slate-500">0 prior attempts</span>
        </div>
        <h2 id="diff-heading" className="mt-2 text-xl font-semibold text-white">
          See What Changed
        </h2>
        <div className="mt-4 rounded-xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center text-sm text-slate-400">
          Run your code at least once. When you modify your code on future attempts, you will see side-by-side line diffs, execution result comparisons, and smart explanations of why the modification helps!
        </div>
      </section>
    );
  }

  const beforePassedCount = previousAttempt
    ? previousAttempt.test_results.filter((r) => r.category === "passed").length
    : 0;
  const beforeTotalCount = previousAttempt ? previousAttempt.test_results.length : 0;

  const afterPassedCount = selectedAttempt
    ? selectedAttempt.test_results.filter((r) => r.category === "passed").length
    : 0;
  const afterTotalCount = selectedAttempt ? selectedAttempt.test_results.length : 0;

  return (
    <section className="panel p-6 sm:p-7" aria-labelledby="diff-heading">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
        <div>
          <span className="eyebrow text-sky-300">Code Evolution & Diff</span>
          <h2 id="diff-heading" className="mt-1 text-xl font-semibold text-white">
            Inspect Code Changes
          </h2>
        </div>

        {/* Attempt selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="attempt-select" className="text-xs text-slate-400">
            Compare:
          </label>
          <select
            id="attempt-select"
            value={selectedAttemptIndex}
            onChange={(e) => setSelectedAttemptIndex(Number(e.target.value))}
            className="rounded-lg border border-white/10 bg-[#0c121b] px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-sky-300/50"
          >
            {attempts.map((att, idx) => (
              <option key={idx} value={idx}>
                Attempt #{attempts.length - idx} {att.passed ? "(Passed ✓)" : "(Failed ✗)"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Execution Results Comparison (Before vs After) */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/[0.04] p-3 text-xs">
          <div className="flex items-center justify-between font-semibold">
            <span className="text-rose-300">Before {previousAttempt ? `(Attempt #${attempts.length - selectedAttemptIndex - 1})` : "(Initial)"}</span>
            <span className={beforePassedCount === beforeTotalCount && beforeTotalCount > 0 ? "text-emerald-300" : "text-rose-300"}>
              {previousAttempt ? `${beforePassedCount}/${beforeTotalCount} Tests Passed` : "No prior attempt"}
            </span>
          </div>
          {previousAttempt ? (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {previousAttempt.test_results.map((r, i) => (
                <span
                  key={i}
                  className={`rounded px-1.5 py-0.5 text-[10px] font-mono ${
                    r.category === "passed" ? "bg-emerald-400/20 text-emerald-300" : "bg-rose-400/20 text-rose-300"
                  }`}
                >
                  {r.name}: {r.category}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-1 text-[11px] text-slate-400">This was the first recorded attempt.</p>
          )}
        </div>

        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] p-3 text-xs">
          <div className="flex items-center justify-between font-semibold">
            <span className="text-emerald-300">After (Attempt #{attempts.length - selectedAttemptIndex})</span>
            <span className={afterPassedCount === afterTotalCount && afterTotalCount > 0 ? "text-emerald-300 font-bold" : "text-amber-300"}>
              {selectedAttempt ? `${afterPassedCount}/${afterTotalCount} Tests Passed` : "—"}
            </span>
          </div>
          {selectedAttempt ? (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {selectedAttempt.test_results.map((r, i) => (
                <span
                  key={i}
                  className={`rounded px-1.5 py-0.5 text-[10px] font-mono ${
                    r.category === "passed" ? "bg-emerald-400/20 text-emerald-300" : "bg-rose-400/20 text-rose-300"
                  }`}
                >
                  {r.name}: {r.category}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {/* Line-by-Line Code Diff */}
      <div className="mt-5 overflow-hidden rounded-xl border border-white/10 bg-[#090e15]">
        <div className="grid border-b border-white/10 text-xs font-semibold sm:grid-cols-2">
          <div className="border-r border-white/10 bg-rose-500/10 px-4 py-2 text-rose-300">
            Before
          </div>
          <div className="bg-emerald-500/10 px-4 py-2 text-emerald-300">
            After
          </div>
        </div>

        <div className="grid font-mono text-xs leading-6 sm:grid-cols-2">
          {/* Before Code Pane */}
          <div className="overflow-x-auto border-r border-white/10 p-3">
            {beforeCode.split("\n").map((line, idx) => {
              const isHighlight = diffData?.before_highlights.includes(idx + 1);
              return (
                <div
                  key={idx}
                  className={`flex px-2 ${
                    isHighlight ? "bg-rose-500/20 text-rose-200" : "text-slate-300"
                  }`}
                >
                  <span className="mr-3 w-5 select-none text-right text-slate-600">{idx + 1}</span>
                  <span className="whitespace-pre">{line || " "}</span>
                </div>
              );
            })}
          </div>

          {/* After Code Pane */}
          <div className="overflow-x-auto p-3">
            {afterCode.split("\n").map((line, idx) => {
              const isHighlight = diffData?.after_highlights.includes(idx + 1);
              return (
                <div
                  key={idx}
                  className={`flex px-2 ${
                    isHighlight ? "bg-emerald-500/20 text-emerald-200" : "text-slate-300"
                  }`}
                >
                  <span className="mr-3 w-5 select-none text-right text-slate-600">{idx + 1}</span>
                  <span className="whitespace-pre">{line || " "}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Explanations and Why this helps Box */}
      {diffData && (diffData.explanations.length > 0 || diffData.why_it_helps.length > 0) ? (
        <div className="mt-5 space-y-3">
          <div className="rounded-xl border border-sky-400/20 bg-sky-400/[0.06] p-4 text-xs leading-6 text-sky-100 sm:text-sm">
            <h4 className="font-bold text-sky-300">What Changed:</h4>
            <ul className="mt-2 list-inside list-disc space-y-1 text-slate-200">
              {diffData.explanations.map((exp, i) => (
                <li key={i}>{exp}</li>
              ))}
            </ul>
          </div>

          {diffData.why_it_helps.length > 0 ? (
            <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/[0.06] p-4 text-xs leading-6 text-emerald-100 sm:text-sm">
              <h4 className="font-bold text-emerald-300">Why this modification helps:</h4>
              <ul className="mt-2 list-inside list-disc space-y-1 text-slate-200">
                {diffData.why_it_helps.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {/* Restore Button */}
      {selectedAttempt ? (
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={() => onRestoreCode(selectedAttempt.submitted_code)}
            className="secondary-button text-xs"
          >
            Load Attempt #{attempts.length - selectedAttemptIndex} into Editor ↺
          </button>
        </div>
      ) : null}
    </section>
  );
}
