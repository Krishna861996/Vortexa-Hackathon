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
    BrowserSubmission, TestResult, DiffAnalysisRequest, DiffAnalysisResponse, StoredAttempt,
)
from .diff_analyzer import analyze_code_diff
from .mentor import ask_mentor
from .unlocks import lock_reason
from .repository import Repository, get_repository
from .auth import Identity, optional_identity, current_identity


app = FastAPI(title="CodeQuest AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


def require_challenge(repository: Repository, challenge_id: str) -> dict:
    challenge = repository.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


def require_learner(repository: Repository, learner_id: str) -> dict:
    learner = repository.get_learner(learner_id)
    if learner is None:
        repository.ensure_learner(learner_id)
        learner = repository.get_learner(learner_id)
    return learner


def require_unlocked(repository: Repository, challenge: dict, learner_id: str) -> None:
    reason = lock_reason(challenge, repository.list_challenges(), repository.list_attempts(learner_id))
    if reason:
        raise HTTPException(status_code=403, detail=reason)


@app.get("/api/challenges", response_model=list[ChallengeSummary])
def list_challenges(repository: Repository = Depends(get_repository), identity: Identity | None = Depends(optional_identity)):
    challenges = repository.list_challenges()
    attempts = repository.list_attempts(identity.id) if identity else []

    from .gamification import get_daily_challenge, get_mission_number_and_title, DIFFICULTY_BASE_XP
    daily = get_daily_challenge(challenges)
    daily_id = daily["id"] if daily else None

    # Calculate stars for solved challenges
    solved_stars: dict[str, int] = {}
    if identity:
        learner = repository.get_learner(identity.id)
        hint_positions = (learner.get("hint_positions") or {}) if learner else {}
        for a in attempts:
            if a.get("passed"):
                ch_id = a.get("challenge_id", "")
                h_used = hint_positions.get(ch_id, 0)
                stars = 3 if h_used == 0 else (2 if h_used <= 2 else 1)
                solved_stars[ch_id] = max(solved_stars.get(ch_id, 0), stars)

    mistake_map: dict[str, str] = {}
    if attempts:
        from .mistakes import detect_recurring_mistakes, CHALLENGES_FOR_MISTAKE
        challenges_by_id = {c["id"]: c for c in challenges}
        recurring = detect_recurring_mistakes(attempts, challenges_by_id)
        solved_ids = {a["challenge_id"] for a in attempts if a["passed"]}
        for m in recurring:
            for ch_id in CHALLENGES_FOR_MISTAKE.get(m.mistake_type, []):
                if ch_id not in solved_ids and ch_id not in mistake_map:
                    mistake_map[ch_id] = f"Recommended to practice: {m.label}"

    summaries = []
    for idx, challenge in enumerate(challenges):
        reason = lock_reason(challenge, challenges, attempts)
        rec_reason = mistake_map.get(challenge["id"])
        mission_num, mission_title = get_mission_number_and_title(challenge["id"], idx, challenge["title"])
        is_daily = (challenge["id"] == daily_id)
        xp_val = DIFFICULTY_BASE_XP.get(challenge.get("difficulty", "beginner"), 100)
        stars = solved_stars.get(challenge["id"], 0)

        summaries.append({
            **challenge,
            "locked": bool(reason),
            "unlock_message": reason,
            "recommended_reason": rec_reason,
            "mission_number": mission_num,
            "mission_title": mission_title,
            "is_daily": is_daily,
            "stars": stars,
            "xp_value": xp_val,
        })
    return summaries


def clean_starter_code(code: str) -> str:
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped in ("count = 0", "total = 0"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    if not cleaned.endswith("pass") and "return" not in cleaned:
        cleaned += "\n    pass"
    return cleaned


@app.get("/api/challenges/{challenge_id}", response_model=ChallengeDetail)
def get_challenge(challenge_id: str, repository: Repository = Depends(get_repository), identity: Identity | None = Depends(optional_identity)):
    challenge = require_challenge(repository, challenge_id)
    all_challenges = repository.list_challenges()
    reason = lock_reason(challenge, all_challenges, repository.list_attempts(identity.id) if identity else [])

    from .gamification import get_daily_challenge, get_mission_number_and_title, DEFAULT_MISSION_STEPS, DIFFICULTY_BASE_XP
    daily = get_daily_challenge(all_challenges)
    is_daily = (challenge_id == daily["id"]) if daily else False

    idx = next((i for i, c in enumerate(all_challenges) if c["id"] == challenge_id), 0)
    mission_num, mission_title = get_mission_number_and_title(challenge_id, idx, challenge["title"])

    hints_used = 0
    stars = 0
    if identity:
        learner = repository.get_learner(identity.id)
        if learner:
            hints_used = (learner.get("hint_positions") or {}).get(challenge_id, 0)
        attempts = repository.list_attempts(identity.id)
        if any(a.get("challenge_id") == challenge_id and a.get("passed") for a in attempts):
            stars = 3 if hints_used == 0 else (2 if hints_used <= 2 else 1)

    return ChallengeDetail(
        id=challenge["id"],
        title=challenge["title"],
        description=challenge["description"],
        difficulty=challenge["difficulty"],
        function_name=challenge["function_name"],
        starter_code=clean_starter_code(challenge["starter_code"]),
        visible_tests=challenge["visible_tests"],
        concept_tags=challenge["concept_tags"],
        hint_count=len(challenge["hints"]),
        locked=bool(reason), unlock_message=reason,
        mission_number=mission_num,
        mission_title=mission_title,
        is_daily=is_daily,
        stars=stars,
        xp_value=DIFFICULTY_BASE_XP.get(challenge.get("difficulty", "beginner"), 100),
        hints_used=hints_used,
        mission_steps=DEFAULT_MISSION_STEPS,
    )


@app.post("/api/challenges/{challenge_id}/practice-attempts", response_model=AttemptResponse)
def save_browser_attempt(
    challenge_id: str,
    submission: BrowserSubmission,
    repository: Repository = Depends(get_repository),
    identity: Identity = Depends(current_identity),
):
    challenge = require_challenge(repository, challenge_id)
    learner = require_learner(repository, identity.id)
    require_unlocked(repository, challenge, identity.id)
    if len(submission.categories) != len(challenge["visible_tests"]):
        raise HTTPException(status_code=422, detail="A result is required for every visible test.")
    # Browser reports are practice evidence, never server-verified hidden-test grades.
    results = [
        TestResult(name=f"visible-{index + 1}", visibility="visible", category=category, execution="browser")
        for index, category in enumerate(submission.categories)
    ]
    passed = all(row.category == "passed" for row in results)
    
    prior_attempts = repository.list_attempts(identity.id)
    already_solved = any(a.get("challenge_id") == challenge_id and a.get("passed") for a in prior_attempts)

    record = repository.save_attempt({
        "challenge_id": challenge_id,
        "learner_id": identity.id,
        "submitted_code": submission.code,
        "test_results": [row.model_dump() for row in results],
        "passed": passed,
        "concepts_practiced": challenge["concept_tags"],
    })

    from .gamification import calculate_challenge_xp, calculate_gamification_state, get_daily_challenge
    all_challenges = repository.list_challenges()
    daily = get_daily_challenge(all_challenges)
    is_daily = (challenge_id == daily["id"]) if daily else False

    hint_positions = learner.get("hint_positions") or {}
    hints_used = hint_positions.get(challenge_id, 0)
    
    earned_xp = 0
    solo_bonus = False
    stars = 0
    if passed:
        earned_xp, solo_bonus, stars = calculate_challenge_xp(
            challenge["difficulty"], hints_used, is_daily=is_daily, already_solved=already_solved
        )

    all_attempts = repository.list_attempts(identity.id)
    g_state = calculate_gamification_state(identity.id, all_attempts, all_challenges, hint_positions)

    return AttemptResponse(
        id=record["id"], challenge_id=challenge_id, passed=passed, results=results,
        concepts_practiced=challenge["concept_tags"], submitted_at=record["submitted_at"],
        failure_explanation=explain_failure(challenge["concept_tags"], results),
        feedback_source="local" if not passed else None,
        earned_xp=earned_xp,
        solo_bonus=solo_bonus,
        hints_used=hints_used,
        stars=stars,
        total_xp=g_state["total_xp"],
        current_level=g_state["current_level"],
        level_name=g_state["level_name"],
    )


@app.get("/api/challenges/{challenge_id}/attempts", response_model=list[StoredAttempt])
def list_challenge_attempts(
    challenge_id: str,
    repository: Repository = Depends(get_repository),
    identity: Identity = Depends(current_identity),
):
    require_challenge(repository, challenge_id)
    require_learner(repository, identity.id)
    attempts = repository.list_attempts(identity.id)
    filtered = [
        StoredAttempt(
            id=a.get("id"),
            challenge_id=a["challenge_id"],
            submitted_code=a.get("submitted_code", ""),
            test_results=[TestResult(**r) for r in a.get("test_results", [])],
            passed=a.get("passed", False),
            submitted_at=datetime.fromisoformat(str(a["submitted_at"]).replace("Z", "+00:00")),
        )
        for a in attempts
        if a.get("challenge_id") == challenge_id
    ]
    return filtered


@app.post("/api/challenges/{challenge_id}/analyze-diff", response_model=DiffAnalysisResponse)
def analyze_diff(
    challenge_id: str,
    request: DiffAnalysisRequest,
    repository: Repository = Depends(get_repository),
    identity: Identity = Depends(current_identity),
):
    challenge = require_challenge(repository, challenge_id)
    analysis = analyze_code_diff(request.before_code, request.after_code, challenge)
    return DiffAnalysisResponse(**analysis)


@app.post("/api/challenges/{challenge_id}/hints/next", response_model=HintResponse)
def next_hint(
    challenge_id: str,
    request: HintRequest,
    repository: Repository = Depends(get_repository),
    identity: Identity = Depends(current_identity),
):
    challenge = require_challenge(repository, challenge_id)
    learner = require_learner(repository, identity.id)
    require_unlocked(repository, challenge, identity.id)
    positions = learner["hint_positions"] or {}
    # A new page visit starts at hint 1; persisted evidence still gates the mentor.
    next_index = request.hint_index if request.hint_index is not None else positions.get(challenge_id, 0)
    hints = challenge["hints"]
    if next_index >= len(hints):
        return HintResponse(hint=None, hint_number=len(hints), total_hints=len(hints), exhausted=True)
    positions[challenge_id] = max(positions.get(challenge_id, 0), next_index + 1)
    repository.update_hint_positions(identity.id, positions)
    return HintResponse(
        hint=hints[next_index], hint_number=next_index + 1,
        total_hints=len(hints), exhausted=next_index + 1 >= len(hints),
    )

@app.post("/api/challenges/{challenge_id}/mentor", response_model=MentorResponse)
def mentor(
    challenge_id: str,
    request: MentorRequest,
    repository: Repository = Depends(get_repository),
    identity: Identity = Depends(current_identity),
):
    challenge = require_challenge(repository, challenge_id)
    learner = require_learner(repository, identity.id)
    require_unlocked(repository, challenge, identity.id)
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
    identity: Identity = Depends(current_identity),
):
    challenge = require_challenge(repository, challenge_id)
    require_learner(repository, identity.id)
    hidden_tests = repository.get_hidden_tests(challenge_id)
    require_unlocked(repository, challenge, identity.id)
    if not hidden_tests:
        raise HTTPException(status_code=503, detail="Challenge tests are not configured")
    try:
        results = runner.grade(challenge, submission.code, hidden_tests)
    except RunnerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    passed = bool(results) and all(result.category == "passed" for result in results)
    
    prior_attempts = repository.list_attempts(identity.id)
    already_solved = any(a.get("challenge_id") == challenge_id and a.get("passed") for a in prior_attempts)

    record = repository.save_attempt({
        "challenge_id": challenge_id,
        "learner_id": identity.id,
        "submitted_code": submission.code,
        "test_results": [result.model_dump(exclude_none=True) for result in results],
        "passed": passed,
        "concepts_practiced": challenge["concept_tags"],
    })

    from .gamification import calculate_challenge_xp, calculate_gamification_state, get_daily_challenge
    all_challenges = repository.list_challenges()
    daily = get_daily_challenge(all_challenges)
    is_daily = (challenge_id == daily["id"]) if daily else False

    learner = repository.get_learner(identity.id)
    hint_positions = (learner.get("hint_positions") or {}) if learner else {}
    hints_used = hint_positions.get(challenge_id, 0)

    earned_xp = 0
    solo_bonus = False
    stars = 0
    if passed:
        earned_xp, solo_bonus, stars = calculate_challenge_xp(
            challenge["difficulty"], hints_used, is_daily=is_daily, already_solved=already_solved
        )

    all_attempts = repository.list_attempts(identity.id)
    g_state = calculate_gamification_state(identity.id, all_attempts, all_challenges, hint_positions)

    return AttemptResponse(
        id=record["id"], challenge_id=challenge_id, passed=passed,
        results=results, concepts_practiced=challenge["concept_tags"],
        submitted_at=record["submitted_at"],
        failure_explanation=explain_failure(challenge["concept_tags"], results),
        feedback_source="local" if not passed else None,
        earned_xp=earned_xp,
        solo_bonus=solo_bonus,
        hints_used=hints_used,
        stars=stars,
        total_xp=g_state["total_xp"],
        current_level=g_state["current_level"],
        level_name=g_state["level_name"],
    )


@app.get("/api/learners/{learner_id}/progress", response_model=LearnerProgress)
def get_progress(learner_id: str, repository: Repository = Depends(get_repository), identity: Identity = Depends(current_identity)):
    if learner_id != identity.id:
        raise HTTPException(403, "You can only view your own progress.")
    learner = require_learner(repository, learner_id)
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
    all_challenges = repository.list_challenges()
    concept_evidence, recommendations = build_concept_progress(attempts, all_challenges)
    from .mistakes import detect_recurring_mistakes
    challenges_by_id = {c["id"]: c for c in all_challenges}
    recurring_mistakes = detect_recurring_mistakes(attempts, challenges_by_id)

    from .gamification import calculate_gamification_state
    hint_positions = (learner.get("hint_positions") or {}) if learner else {}
    g_state = calculate_gamification_state(learner_id, attempts, all_challenges, hint_positions)

    return LearnerProgress(
        learner_id=learner_id,
        total_attempts=len(attempts),
        solved_challenges=sum(item.solved for item in challenges),
        concepts_practiced=sorted(concepts),
        challenges=challenges,
        concepts=concept_evidence,
        recommendations=recommendations,
        recurring_mistakes=recurring_mistakes,
        total_xp=g_state["total_xp"],
        current_level=g_state["current_level"],
        level_name=g_state["level_name"],
        next_level_xp=g_state["next_level_xp"],
        level_progress_pct=g_state["level_progress_pct"],
        daily_challenge_id=g_state["daily_challenge_id"],
        daily_challenge_title=g_state["daily_challenge_title"],
        daily_challenge_completed=g_state["daily_challenge_completed"],
        daily_streak=g_state["daily_streak"],
        badges=g_state["badges"],
        progress_map=g_state["progress_map"],
    )


@app.get("/api/me/progress", response_model=LearnerProgress)
def my_progress(repository: Repository = Depends(get_repository), identity: Identity = Depends(current_identity)):
    return get_progress(identity.id, repository, identity)

