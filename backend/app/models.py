from datetime import datetime
from typing import Literal, Any

from pydantic import BaseModel, Field


Difficulty = Literal["beginner", "easy", "medium", "hard", "advanced"]
ResultCategory = Literal["passed", "wrong output", "runtime error", "timeout"]
ConceptStatus = Literal["not started", "practicing", "improving", "demonstrated"]
ProgressOutcome = ResultCategory | Literal["unknown"]


class TestCase(BaseModel):
    input: list[int | str | bool | list[int]]
    expected: int | str | bool


class AchievementBadge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked: bool = False
    unlocked_at: str | None = None


class MissionMapNode(BaseModel):
    mission_number: int
    challenge_id: str
    title: str
    difficulty: Difficulty
    status: Literal["locked", "available", "current", "completed"]
    stars: int = 0
    xp_earned: int = 0
    is_daily: bool = False


class ChallengeSummary(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    concept_tags: list[str]
    locked: bool = False
    unlock_message: str | None = None
    recommended_reason: str | None = None
    mission_number: int = 1
    mission_title: str | None = None
    is_daily: bool = False
    stars: int = 0
    xp_value: int = 100


class ChallengeDetail(ChallengeSummary):
    description: str
    function_name: str
    starter_code: str
    visible_tests: list[TestCase]
    hint_count: int
    hints_used: int = 0
    mission_steps: list[str] = []


class HintRequest(BaseModel):
    hint_index: int | None = Field(default=None, ge=0)


class HintResponse(BaseModel):
    hint: str | None
    hint_number: int
    total_hints: int
    exhausted: bool


class MentorRequest(BaseModel):
    mode: Literal["guidance", "deep_hint", "solution"] = "guidance"
    code: str = Field(default="", max_length=6000)
    question: str = Field(min_length=1, max_length=1000)


class MentorResponse(BaseModel):
    answer: str
    source: Literal["gemini", "local"]


class Submission(BaseModel):
    code: str = Field(min_length=1, max_length=6000)


class TestResult(BaseModel):
    name: str
    visibility: Literal["visible", "hidden"]
    category: ResultCategory
    execution: Literal["server", "browser"] = "server"


class BrowserSubmission(Submission):
    categories: list[ResultCategory] = Field(min_length=1, max_length=100)


class AttemptResponse(BaseModel):
    id: int
    challenge_id: str
    passed: bool
    results: list[TestResult]
    concepts_practiced: list[str]
    submitted_at: datetime
    failure_explanation: str | None = None
    feedback_source: Literal["local"] | None = None
    earned_xp: int = 0
    solo_bonus: bool = False
    hints_used: int = 0
    stars: int = 0
    total_xp: int = 0
    current_level: int = 1
    level_name: str = "Novice Coder"
    new_badges: list[str] = []


class ChallengeProgress(BaseModel):
    challenge_id: str
    attempts: int
    solved: bool
    last_submitted_at: datetime


class RecurringMistake(BaseModel):
    mistake_type: str
    label: str
    description: str
    occurrences: int
    affected_challenges: list[str]
    focus_advice: str


class ConceptProgress(BaseModel):
    concept: str
    status: ConceptStatus
    attempts: int
    passed_attempts: int
    distinct_passing_solutions: int
    completed_challenges: int
    available_challenges: int
    recent_results: list[ProgressOutcome]
    demonstrated_skills: list[str] = []


class PracticeRecommendation(BaseModel):
    concept: str
    repeated_category: str
    challenge_id: str
    challenge_title: str
    reason: str
    adapted_for: str | None = None


class LearnerProgress(BaseModel):
    learner_id: str
    total_attempts: int
    solved_challenges: int
    concepts_practiced: list[str]
    challenges: list[ChallengeProgress]
    concepts: list[ConceptProgress]
    recommendations: list[PracticeRecommendation]
    recurring_mistakes: list[RecurringMistake] = []
    total_xp: int = 0
    current_level: int = 1
    level_name: str = "Novice Coder"
    next_level_xp: int = 150
    level_progress_pct: int = 0
    daily_challenge_id: str | None = None
    daily_challenge_title: str | None = None
    daily_challenge_completed: bool = False
    daily_streak: int = 0
    badges: list[AchievementBadge] = []
    progress_map: list[MissionMapNode] = []


class DiffAnalysisRequest(BaseModel):
    before_code: str = Field(max_length=10000)
    after_code: str = Field(max_length=10000)


class DiffAnalysisResponse(BaseModel):
    diff_hunks: list[dict[str, Any]]
    before_highlights: list[int]
    after_highlights: list[int]
    explanations: list[str]
    why_it_helps: list[str]


class StoredAttempt(BaseModel):
    id: int | None = None
    challenge_id: str
    submitted_code: str
    test_results: list[TestResult]
    passed: bool
    submitted_at: datetime

