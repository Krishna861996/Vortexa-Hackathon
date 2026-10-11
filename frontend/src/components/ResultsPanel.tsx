import type { AttemptResponse, TestCategory } from "@/lib/api";

const categoryStyle: Record<TestCategory, string> = {
  passed: "border-emerald-300/20 bg-emerald-300/[0.07] text-emerald-200",
  "wrong output": "border-amber-300/20 bg-amber-300/[0.07] text-amber-200",
  "runtime error": "border-rose-300/20 bg-rose-300/[0.07] text-rose-200",
  timeout: "border-violet-300/20 bg-violet-300/[0.07] text-violet-200",
};

const categoryHelp: Record<TestCategory, string> = {
  passed: "Your solution returned the expected output.",
  "wrong output": "Your code ran, but the output did not match.",
  "runtime error": "Your code stopped with an error while running.",
  timeout: "Your code exceeded the time limit.",
};

export function ResultsPanel({ attempt, running, error, onRetry }: { attempt: AttemptResponse | null; running: boolean; error: string; onRetry: () => void }) {
  return (
    <section className="panel overflow-hidden" aria-labelledby="results-heading" aria-live="polite">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4 sm:px-6">
        <div><p className="text-[11px] font-bold uppercase tracking-[.16em] text-slate-500">Feedback</p><h2 id="results-heading" className="mt-1 text-lg font-semibold text-white">Test results</h2></div>
        {attempt ? <span className={`rounded-full px-3 py-1 text-xs font-bold ${attempt.passed ? "bg-emerald-300/10 text-emerald-200" : "bg-amber-300/10 text-amber-200"}`}>{attempt.results.filter((result) => result.category === "passed").length}/{attempt.results.length} passed</span> : null}
      </div>
      <div className="p-5 sm:p-6">
        {running ? <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] p-5 text-sm text-slate-300"><span className="h-4 w-4 animate-spin rounded-full border-2 border-lime-300/20 border-t-lime-300 motion-reduce:animate-none" aria-hidden="true" />Running your Python tests…</div> : null}
        {!running && error ? <div role="alert" className="rounded-xl border border-rose-300/20 bg-rose-300/[0.07] p-4 text-sm leading-6 text-rose-100"><strong className="block font-semibold">Could not run the tests</strong>{error}</div> : null}
        {!running && !error && !attempt ? <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.025] px-5 py-10 text-center"><span className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-lime-300/10 font-mono text-lg text-lime-300" aria-hidden="true">&gt;_</span><p className="mt-4 font-semibold text-white">Ready when you are</p><p className="mt-1 text-sm text-slate-400">Run your code to see a result for every test.</p></div> : null}
        {!running && !error && attempt ? <div className="space-y-3">
          {!attempt.passed && attempt.failure_explanation ? <div className="rounded-xl border border-lime-300/20 bg-lime-300/[0.055] p-5">
            <p className="text-[11px] font-bold uppercase tracking-[.14em] text-lime-300">{attempt.feedback_source === "local" ? "Local guidance" : "Guidance"}</p>
            <p className="mt-2 text-sm leading-6 text-slate-200">{attempt.failure_explanation}</p>
            <button type="button" className="secondary-button mt-4" onClick={onRetry}>Edit and retry <span aria-hidden="true">→</span></button>
          </div> : null}
          {attempt.results.map((result) => <div key={result.name} className={`flex flex-col gap-3 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between ${categoryStyle[result.category]}`}>
            <div className="flex items-start gap-3"><span className="mt-0.5 flex h-6 w-6 flex-none items-center justify-center rounded-full border border-current text-xs font-bold" aria-hidden="true">{result.category === "passed" ? "✓" : "!"}</span><div><p className="font-semibold text-white">{result.visibility === "hidden" ? "Hidden test" : "Visible test"} {result.name.split("-").at(-1)}</p><p className="mt-0.5 text-xs leading-5 opacity-90">{categoryHelp[result.category]}</p></div></div>
            <span className="self-start whitespace-nowrap rounded-lg bg-black/15 px-2.5 py-1.5 text-xs font-bold capitalize sm:self-center">{result.category}</span>
          </div>)}
          <p className="pt-1 text-xs leading-5 text-slate-500">{attempt.results.some((result) => result.execution === "browser") ? "Practice results saved. Only visible tests were checked in your browser." : "Hidden test cases stay private. Their results show only the outcome."}</p>
        </div> : null}
      </div>
    </section>
  );
}
