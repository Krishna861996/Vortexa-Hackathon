import type { ChallengeDetail, TestResult } from "./api";

type Pyodide = { runPythonAsync: (code: string) => Promise<unknown> };
let pyodidePromise: Promise<Pyodide> | null = null;

declare global {
  interface Window { loadPyodide?: (options: { indexURL: string }) => Promise<Pyodide>; }
}

function loadPyodide(): Promise<Pyodide> {
  if (pyodidePromise) return pyodidePromise;
  pyodidePromise = new Promise((resolve, reject) => {
    const start = () => window.loadPyodide
      ? window.loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/" }).then(resolve, reject)
      : reject(new Error("Pyodide could not load. Check your internet connection and try again."));
    if (window.loadPyodide) return start();
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js";
    script.onload = start;
    script.onerror = () => reject(new Error("Pyodide could not load. Check your internet connection and try again."));
    document.head.appendChild(script);
  });
  return pyodidePromise;
}

export async function runVisibleTests(challenge: ChallengeDetail, source: string): Promise<TestResult[]> {
  const pyodide = await loadPyodide();
  const results: TestResult[] = [];
  for (const [index, test] of challenge.visible_tests.entries()) {
    const input = JSON.stringify(test.input).replaceAll("\\", "\\\\").replaceAll("'", "\\'");
    const expected = JSON.stringify(test.expected).replaceAll("\\", "\\\\").replaceAll("'", "\\'");
    const script = `${source}\nimport json\n_args = json.loads('${input}')\n_expected = json.loads('${expected}')\ntry:\n    _actual = ${challenge.function_name}(*_args)\n    _result = json.dumps({'ok': True, 'same': type(_actual) is type(_expected) and _actual == _expected})\nexcept Exception:\n    _result = json.dumps({'ok': False, 'same': False})\n_result`;
    try {
      const raw = String(await pyodide.runPythonAsync(script));
      const result = JSON.parse(raw.trim()) as { ok: boolean; same: boolean };
      results.push({ name: `visible-${index + 1}`, visibility: "visible", category: result.ok ? (result.same ? "passed" : "wrong output") : "runtime error" });
    } catch {
      results.push({ name: `visible-${index + 1}`, visibility: "visible", category: "runtime error" });
    }
  }
  return results;
}
