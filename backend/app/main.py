from collections import defaultdict
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .feedback import explain_failure
from .progress import build_concept_progress
from .runner import RunnerUnavailable, get_runner
from .models import (
    AttemptResponse, ChallengeDetail, ChallengeProgress, ChallengeSummary,
    HintRequest, HintResponse, LearnerProgress, Submission, MentorRequest, MentorResponse,
)
from .mentor import ask_mentor
from .repository import Repository, get_repository


app = FastAPI(title="CodeQuest AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def require_challenge(repository: Repository, challenge_id: str) -> dict:
    challenge = repository.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


def require_learner(repository: Repository, learner_id: str) -> dict:
    learner = repository.get_learner(learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner


@app.get("/api/challenges", response_model=list[ChallengeSummary])
def list_challenges(repository: Repository = Depends(get_repository)):
    return repository.list_challenges()


@app.get("/api/challenges/{challenge_id}", response_model=ChallengeDetail)
def get_challenge(challenge_id: str, repository: Repository = Depends(get_repository)):
    challenge = require_challenge(repository, challenge_id)
    return ChallengeDetail(
        id=challenge["id"],
        title=challenge["title"],
        description=challenge["description"],
        difficulty=challenge["difficulty"],
        function_name=challenge["function_name"],
        starter_code=challenge["starter_code"],
        visible_tests=challenge["visible_tests"],
        concept_tags=challenge["concept_tags"],
        hint_count=len(challenge["hints"]),
    )


@app.post("/api/challenges/{challenge_id}/hints/next", response_model=HintResponse)
def next_hint(
    challenge_id: str,
    request: HintRequest,
    repository: Repository = Depends(get_repository),
):
    challenge = require_challenge(repository, challenge_id)
    learner = require_learner(repository, request.learner_id)
    positions = learner["hint_positions"] or {}
    # A new page visit starts at hint 1; persisted evidence still gates the mentor.
    next_index = request.hint_index if request.hint_index is not None else positions.get(challenge_id, 0)
    hints = challenge["hints"]
    if next_index >= len(hints):
        return HintResponse(hint=None, hint_number=len(hints), total_hints=len(hints), exhausted=True)
    positions[challenge_id] = max(positions.get(challenge_id, 0), next_index + 1)
    repository.update_hint_positions(request.learner_id, positions)
    return HintResponse(
        hint=hints[next_index], hint_number=next_index + 1,
        total_hints=len(hints), exhausted=next_index + 1 >= len(hints),
    )

@app.post("/api/challenges/{challenge_id}/mentor", response_model=MentorResponse)
def mentor(
    challenge_id: str,
    request: MentorRequest,
    repository: Repository = Depends(get_repository),
):
    challenge = require_challenge(repository, challenge_id)
    learner = require_learner(repository, request.learner_id)
    positions = learner["hint_positions"] or {}
    if positions.get(challenge_id, 0) < len(challenge["hints"]):
        raise HTTPException(status_code=403, detail="Reveal all hints before asking the mentor for help.")
    return ask_mentor(challenge, request.question, request.code, request.mode)


@app.post("/api/challenges/{challenge_id}/attempts", response_model=AttemptResponse)
def submit_code(
    challenge_id: str,
    submission: Submission,
    repository: Repository = Depends(get_repository),
    runner=Depends(get_runner),
):
    challenge = require_challenge(repository, challenge_id)
    require_learner(repository, submission.learner_id)
    hidden_tests = repository.get_hidden_tests(challenge_id)
    if not hidden_tests:
        raise HTTPException(status_code=503, detail="Challenge tests are not configured")
    try:
        results = runner.grade(challenge, submission.code, hidden_tests)
    except RunnerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    passed = bool(results) and all(result.category == "passed" for result in results)
    record = repository.save_attempt({
        "challenge_id": challenge_id,
        "learner_id": submission.learner_id,
        "submitted_code": submission.code,
        "test_results": [result.model_dump(exclude_none=True) for result in results],
        "passed": passed,
        "concepts_practiced": challenge["concept_tags"],
    })
    return AttemptResponse(
        id=record["id"], challenge_id=challenge_id, passed=passed,
        results=results, concepts_practiced=challenge["concept_tags"],
        submitted_at=record["submitted_at"],
        failure_explanation=explain_failure(challenge["concept_tags"], results),
        feedback_source="local" if not passed else None,
    )


@app.get("/api/learners/{learner_id}/progress", response_model=LearnerProgress)
def get_progress(learner_id: str, repository: Repository = Depends(get_repository)):
    require_learner(repository, learner_id)
    attempts = repository.list_attempts(learner_id)
    grouped: dict[str, list[dict]] = defaultdict(list)
    concepts = set()
    for attempt in attempts:
        grouped[attempt["challenge_id"]].append(attempt)
        concepts.update(attempt["concepts_practiced"])
    challenges = [
        ChallengeProgress(
            challenge_id=challenge_id,
            attempts=len(rows),
            solved=any(row["passed"] for row in rows),
            last_submitted_at=datetime.fromisoformat(rows[0]["submitted_at"].replace("Z", "+00:00")),
        )
        for challenge_id, rows in grouped.items()
    ]
    concept_evidence, recommendations = build_concept_progress(attempts, repository.list_challenges())
    return LearnerProgress(
        learner_id=learner_id,
        total_attempts=len(attempts),
        solved_challenges=sum(item.solved for item in challenges),
        concepts_practiced=sorted(concepts),
        challenges=challenges,
        concepts=concept_evidence,
        recommendations=recommendations,
    )
