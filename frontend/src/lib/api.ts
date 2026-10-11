import { getSupabase } from "./supabase";
export type Difficulty = "beginner" | "easy" | "medium" | "hard" | "advanced";
export type TestCategory = "passed" | "wrong output" | "runtime error" | "timeout";

export interface AchievementBadge {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
  unlocked_at?: string | null;
}

export interface MissionMapNode {
  mission_number: number;
  challenge_id: string;
  title: string;
  difficulty: Difficulty;
  status: "locked" | "available" | "current" | "completed";
  stars: number;
  xp_earned: number;
  is_daily: boolean;
}

export interface ChallengeSummary {
  locked: boolean;
  unlock_message: string | null;
  recommended_reason?: string | null;
  id: string;
  title: string;
  difficulty: Difficulty;
  concept_tags: string[];
  mission_number?: number;
  mission_title?: string | null;
  is_daily?: boolean;
  stars?: number;
  xp_value?: number;
}

export interface VisibleTest {
  input: Array<number | string | boolean | number[]>;
  expected: number | string | boolean;
}

export interface ChallengeDetail extends ChallengeSummary {
  description: string;
  function_name: string;
  starter_code: string;
  visible_tests: VisibleTest[];
  hint_count: number;
  hints_used?: number;
  mission_steps?: string[];
}

export interface HintResponse {
  hint: string | null;
  hint_number: number;
  total_hints: number;
  exhausted: boolean;
}
export interface MentorResponse { answer: string; source: "gemini" | "local"; }

export interface TestResult {
  execution?: "browser" | "server";
  name: string;
  visibility: "visible" | "hidden";
  category: TestCategory;
}

export interface AttemptResponse {
  id: number;
  challenge_id: string;
  passed: boolean;
  results: TestResult[];
  concepts_practiced: string[];
  submitted_at: string;
  failure_explanation: string | null;
  feedback_source: "local" | null;
  earned_xp?: number;
  solo_bonus?: boolean;
  hints_used?: number;
  stars?: number;
  total_xp?: number;
  current_level?: number;
  level_name?: string;
  new_badges?: string[];
}

export interface ChallengeProgress {
  challenge_id: string;
  attempts: number;
  solved: boolean;
  last_submitted_at: string;
}

export type ConceptStatus = "not started" | "practicing" | "improving" | "demonstrated";
export type ProgressOutcome = TestCategory | "unknown";

export interface ConceptProgress {
  concept: string;
  status: ConceptStatus;
  attempts: number;
  passed_attempts: number;
  distinct_passing_solutions: number;
  completed_challenges: number;
  available_challenges: number;
  recent_results: ProgressOutcome[];
  demonstrated_skills?: string[];
}

export interface RecurringMistake {
  mistake_type: string;
  label: string;
  description: string;
  occurrences: number;
  affected_challenges: string[];
  focus_advice: string;
}

export interface PracticeRecommendation {
  concept: string;
  repeated_category: string;
  challenge_id: string;
  challenge_title: string;
  reason: string;
  adapted_for?: string;
}

export interface LearnerProgress {
  learner_id: string;
  total_attempts: number;
  solved_challenges: number;
  concepts_practiced: string[];
  challenges: ChallengeProgress[];
  concepts: ConceptProgress[];
  recommendations: PracticeRecommendation[];
  recurring_mistakes?: RecurringMistake[];
  total_xp?: number;
  current_level?: number;
  level_name?: string;
  next_level_xp?: number;
  level_progress_pct?: number;
  daily_challenge_id?: string | null;
  daily_challenge_title?: string | null;
  daily_challenge_completed?: boolean;
  daily_streak?: number;
  badges?: AchievementBadge[];
  progress_map?: MissionMapNode[];
}

export const DIFFICULTY_ORDER: Difficulty[] = ["beginner", "easy", "medium", "hard", "advanced"];

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const session = await getSupabase()?.auth.getSession();
  const token = session?.data.session?.access_token;
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init?.headers },
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(`Could not reach the CodeQuest API at ${baseUrl}. Check that FastAPI is running.`);
  }

  if (!response.ok) {
    let detail = "The request could not be completed.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Keep the simple fallback when the server returns no JSON body.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export interface DiffHunk {
  type: "equal" | "added" | "removed";
  before_line: number | null;
  after_line: number | null;
  text: string;
}

export interface DiffAnalysisResponse {
  diff_hunks: DiffHunk[];
  before_highlights: number[];
  after_highlights: number[];
  explanations: string[];
  why_it_helps: string[];
}

export interface StoredAttempt {
  id?: number | null;
  challenge_id: string;
  submitted_code: string;
  test_results: TestResult[];
  passed: boolean;
  submitted_at: string;
}

export const api = {
  savePractice: (id: string, code: string, results: TestResult[]) =>
    request<AttemptResponse>(`/api/challenges/${encodeURIComponent(id)}/practice-attempts`, { method: "POST", body: JSON.stringify({ code, categories: results.map((row) => row.category) }) }),
  listChallenges: (signal?: AbortSignal) => request<ChallengeSummary[]>("/api/challenges", { signal }),
  getChallenge: (id: string, signal?: AbortSignal) =>
    request<ChallengeDetail>(`/api/challenges/${encodeURIComponent(id)}`, { signal }),
  getChallengeAttempts: (id: string, signal?: AbortSignal) =>
    request<StoredAttempt[]>(`/api/challenges/${encodeURIComponent(id)}/attempts`, { signal }),
  analyzeDiff: (id: string, beforeCode: string, afterCode: string) =>
    request<DiffAnalysisResponse>(`/api/challenges/${encodeURIComponent(id)}/analyze-diff`, {
      method: "POST",
      body: JSON.stringify({ before_code: beforeCode, after_code: afterCode }),
    }),
  nextHint: (id: string, hintIndex: number) =>
    request<HintResponse>(`/api/challenges/${encodeURIComponent(id)}/hints/next`, {
      method: "POST",
      body: JSON.stringify({ hint_index: hintIndex }),
    }),
  mentor: (id: string, code: string, question: string, mode: "guidance" | "deep_hint" | "solution" = "guidance") =>
    request<MentorResponse>(`/api/challenges/${encodeURIComponent(id)}/mentor`, { method: "POST", body: JSON.stringify({ code, question, mode }) }),
  submit: (id: string, code: string) =>
    request<AttemptResponse>(`/api/challenges/${encodeURIComponent(id)}/attempts`, {
      method: "POST",
      body: JSON.stringify({ code }),
    }),
  getProgress: (signal?: AbortSignal) =>
    request<LearnerProgress>("/api/me/progress", { signal }),
};

export function formatConcept(concept: string): string {
  return concept.replace(/-/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}
