from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Difficulty = Literal["beginner", "easy", "medium", "hard", "advanced"]
ResultCategory = Literal["passed", "wrong output", "runtime error", "timeout"]
ConceptStatus = Literal["not started", "practicing", "improving", "demonstrated"]
ProgressOutcome = ResultCategory | Literal["unknown"]


class TestCase(BaseModel):
    input: list[int | str | bool | list[int]]
    expected: int | str | bool


class ChallengeSummary(BaseModel):
    id: str
    title: str
    difficulty: Difficulty
    concept_tags: list[str]


class ChallengeDetail(ChallengeSummary):
    description: str
    function_name: str
    starter_code: str
    visible_tests: list[TestCase]
    hint_count: int


class HintRequest(BaseModel):
    learner_id: str = "demo-learner"


class HintResponse(BaseModel):
    hint: str | None
    hint_number: int
    total_hints: int
    exhausted: bool


class Submission(BaseModel):
    learner_id: str = "demo-learner"
    code: str = Field(min_length=1, max_length=6000)


class TestResult(BaseModel):
    name: str
    visibility: Literal["visible", "hidden"]
    category: ResultCategory


class AttemptResponse(BaseModel):
    id: int
    challenge_id: str
    passed: bool
    results: list[TestResult]
    concepts_practiced: list[str]
    submitted_at: datetime
    failure_explanation: str | None = None
    feedback_source: Literal["local"] | None = None


class ChallengeProgress(BaseModel):
    challenge_id: str
    attempts: int
    solved: bool
    last_submitted_at: datetime


class ConceptProgress(BaseModel):
    concept: str
    status: ConceptStatus
    attempts: int
    passed_attempts: int
    distinct_passing_solutions: int
    completed_challenges: int
    available_challenges: int
    recent_results: list[ProgressOutcome]


class PracticeRecommendation(BaseModel):
    concept: str
    repeated_category: Literal["wrong output", "runtime error", "timeout"]
    challenge_id: str
    challenge_title: str
    reason: str


class LearnerProgress(BaseModel):
    learner_id: str
    total_attempts: int
    solved_challenges: int
    concepts_practiced: list[str]
    challenges: list[ChallengeProgress]
    concepts: list[ConceptProgress]
    recommendations: list[PracticeRecommendation]

