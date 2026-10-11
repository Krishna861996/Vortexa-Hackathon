"""Simple, explainable concept evidence and practice recommendations."""

import ast
from collections import Counter
from hashlib import sha256
from typing import Any

from .models import ConceptProgress, PracticeRecommendation, ProgressOutcome


DIFFICULTY_RANK = {"beginner": 0, "easy": 1, "medium": 2, "hard": 3, "advanced": 4}
FAILURE_PRIORITY = {"timeout": 0, "runtime error": 1, "wrong output": 2}


def attempt_outcome(attempt: dict[str, Any]) -> ProgressOutcome:
    if attempt["passed"]:
        return "passed"
    counts = Counter(
        result.get("category")
        for result in attempt.get("test_results", [])
        if result.get("category") in FAILURE_PRIORITY
    )
    if not counts:
        return "unknown"
    return sorted(counts, key=lambda category: (-counts[category], FAILURE_PRIORITY[category]))[0]


def solution_fingerprint(attempt: dict[str, Any]) -> str:
    code = attempt.get("submitted_code", "")
    try:
        normalized = ast.dump(ast.parse(code), include_attributes=False)
    except (SyntaxError, ValueError):
        normalized = "\n".join(line.rstrip() for line in code.splitlines()).strip()
    return sha256(f"{attempt['challenge_id']}\n{normalized}".encode()).hexdigest()


from .mistakes import (
    get_demonstrated_skills_for_concept,
    detect_recurring_mistakes,
    adapt_recommendations_for_mistakes,
)


def build_concept_progress(
    attempts: list[dict[str, Any]], challenges: list[dict[str, Any]],
) -> tuple[list[ConceptProgress], list[PracticeRecommendation]]:
    # Repository rows arrive newest first. Keep one outcome per submission,
    # so a challenge with many tests cannot outweigh another challenge.
    solved_ids = {attempt["challenge_id"] for attempt in attempts if attempt["passed"]}
    concepts = sorted({tag for challenge in challenges for tag in challenge["concept_tags"]})
    evidence: list[ConceptProgress] = []
    recommendations: list[PracticeRecommendation] = []

    for concept in concepts:
        relevant = [attempt for attempt in attempts if concept in attempt["concepts_practiced"]]
        passes = [attempt for attempt in relevant if attempt["passed"]]
        distinct_passes = len({solution_fingerprint(attempt) for attempt in passes})
        recent = [attempt_outcome(attempt) for attempt in relevant[:3]]
        available = [challenge for challenge in challenges if concept in challenge["concept_tags"]]

        if not relevant:
            status = "not started"
        elif len(relevant) >= 3 and distinct_passes >= 2 and recent.count("passed") >= 2:
            status = "demonstrated"
        elif len(relevant) >= 2 and recent[0] == "passed":
            status = "improving"
        else:
            status = "practicing"

        demonstrated_skills = get_demonstrated_skills_for_concept(concept, solved_ids)

        evidence.append(ConceptProgress(
            concept=concept, status=status, attempts=len(relevant),
            passed_attempts=len(passes), distinct_passing_solutions=distinct_passes,
            completed_challenges=len({attempt["challenge_id"] for attempt in passes}),
            available_challenges=len(available), recent_results=recent,
            demonstrated_skills=demonstrated_skills,
        ))

        if (
            len(relevant) < 2
            or recent[0] not in FAILURE_PRIORITY
            or recent[0] != recent[1]
            or solution_fingerprint(relevant[0]) == solution_fingerprint(relevant[1])
        ):
            continue

        candidates = sorted(
            available,
            key=lambda challenge: (
                challenge["id"] in solved_ids,
                DIFFICULTY_RANK[challenge["difficulty"]],
                challenge["title"],
            ),
        )
        if not candidates:
            continue
        choice = candidates[0]
        action = "Retry" if choice["id"] == relevant[0]["challenge_id"] else "Try"
        recommendations.append(PracticeRecommendation(
            concept=concept, repeated_category=recent[0],
            challenge_id=choice["id"], challenge_title=choice["title"],
            reason=(
                f"Your two latest attempts with different code involving {concept.replace('-', ' ')} both ended with "
                f"{recent[0]}. {action} {choice['title']} ({choice['difficulty']}) "
                f"to practice that concept with a focused task."
            ),
        ))

    # Detect recurring mistakes across all attempts and adapt future challenges to them
    challenges_by_id = {c["id"]: c for c in challenges}
    recurring = detect_recurring_mistakes(attempts, challenges_by_id)
    adapted = adapt_recommendations_for_mistakes(recurring, challenges, solved_ids)

    # Combine concept recommendations with adapted mistake recommendations
    seen_challenges = {item.challenge_id for item in recommendations}
    combined_recommendations = recommendations + [a for a in adapted if a.challenge_id not in seen_challenges]

    return evidence, combined_recommendations
