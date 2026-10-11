"""Detection of recurring mistakes and adaptation of practice challenges."""

import ast
from typing import Any
from .models import RecurringMistake, PracticeRecommendation


SKILLS_BY_CHALLENGE: dict[str, dict[str, list[str]]] = {
    "add-numbers": {
        "functions": ["Function signature & return value"],
        "arithmetic": ["Integer addition", "Signed arithmetic"],
    },
    "is-even": {
        "modulo": ["Remainder operator (%)", "Divisibility by 2"],
        "booleans": ["Boolean return expression"],
    },
    "reverse-text": {
        "strings": ["Character sequence handling", "Empty string preservation"],
        "slicing": ["Step slicing with negative step ([::-1])"],
    },
    "count-vowels": {
        "loops": ["Character-by-character iteration", "Accumulator counter"],
        "strings": ["Case normalization (.lower())", "Membership testing"],
        "conditionals": ["Vowel inclusion check"],
    },
    "fizz-buzz": {
        "conditionals": ["Order-dependent branches", "Combined condition precedence"],
        "modulo": ["Multi-factor divisibility"],
        "strings": ["Type conversion to string (str(n))"],
    },
    "sum-list": {
        "lists": ["List traversal", "Empty list handling"],
        "loops": ["Running sum accumulation"],
        "arithmetic": ["Zero identity element"],
    },
    "say-hello": {
        "functions": ["String formatting in functions"],
        "strings": ["f-string interpolation or concatenation"],
    },
    "double-number": {
        "functions": ["Pure function arithmetic"],
        "arithmetic": ["Scaling numbers", "Negative factor handling"],
    },
    "rectangle-area": {
        "functions": ["Multi-parameter functions"],
        "arithmetic": ["Geometric product", "Zero boundary handling"],
    },
    "last-character": {
        "strings": ["Negative indexing ([-1])", "Empty string guard"],
        "conditionals": ["Short-circuit emptiness check"],
    },
    "larger-number": {
        "conditionals": ["Binary comparison (>=)", "Equality fallback"],
        "functions": ["Exhaustive conditional returns"],
    },
    "absolute-value": {
        "conditionals": ["Sign testing (< 0)", "Branch negation"],
        "arithmetic": ["Unary negation"],
    },
    "count-positive": {
        "lists": ["List filtering"],
        "loops": ["Conditional accumulation"],
        "conditionals": ["Strict inequality (> 0)"],
    },
    "palindrome": {
        "strings": ["Two-way equality", "Case folding"],
        "slicing": ["Full string reversal"],
        "booleans": ["Symmetric comparison"],
    },
    "word-count": {
        "strings": ["Whitespace splitting (.split())", "Blank text edge case"],
        "lists": ["Collection sizing (len())"],
    },
    "largest-item": {
        "lists": ["Negative list handling", "Empty list guard"],
        "loops": ["Extremum tracking"],
        "conditionals": ["Running maximum comparison"],
    },
    "make-initials": {
        "strings": ["First character extraction", "Case transformation (.upper())"],
        "lists": ["Word iteration"],
        "loops": ["Initial aggregation"],
    },
    "second-largest": {
        "lists": ["Distinct value extraction", "Element counting"],
        "sorting": ["Sorted list indexing"],
        "conditionals": ["Cardinality checks (< 2 items)"],
    },
    "longest-word": {
        "strings": ["String length comparison", "Tie-breaking preserves first"],
        "loops": ["Extremum tracking by property"],
        "conditionals": ["Strict improvement check (> len)"],
    },
    "compress-runs": {
        "strings": ["Adjacent character comparison", "Run compression"],
        "loops": ["Consecutive duplicate filtering"],
        "conditionals": ["Previous-element comparison"],
    },
    "balanced-parentheses": {
        "strings": ["Parentheses tracking", "Order validation"],
        "loops": ["Running balance counter"],
        "conditionals": ["Early negative balance detection"],
    },
    "is-prime": {
        "loops": ["Trial division loop"],
        "modulo": ["Divisor check"],
        "conditionals": ["Small primes and negative boundary guards"],
        "arithmetic": ["Square root upper bound"],
    },
}

CHALLENGES_FOR_MISTAKE: dict[str, list[str]] = {
    "unhandled_empty_input": ["last-character", "reverse-text", "sum-list", "palindrome", "word-count"],
    "off_by_one": ["count-vowels", "last-character", "reverse-text", "second-largest", "compress-runs"],
    "type_mismatch": ["fizz-buzz", "is-even", "say-hello", "larger-number"],
    "unbounded_loop": ["sum-list", "count-vowels", "is-prime", "balanced-parentheses"],
}


def _analyze_code_patterns(code: str) -> set[str]:
    patterns: set[str] = set()
    if not code:
        return patterns

    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return patterns

    has_empty_guard = False
    has_direct_subscript = False

    for node in ast.walk(tree):
        # Look for direct indexing without checking length/truthiness
        if isinstance(node, ast.Subscript):
            has_direct_subscript = True

        # Look for guards like: if not x: return ... or if len(x) == 0: return ...
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                has_empty_guard = True
            elif isinstance(test, ast.Compare):
                # len(x) == 0 or len(x) < 1
                for comparator in test.comparators:
                    if isinstance(comparator, ast.Constant) and comparator.value in (0, 1):
                        has_empty_guard = True

        # Look for off-by-one loop ranges: range(len(x) + 1) or range(len(x) - 1)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "range":
            for arg in node.args:
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Add, ast.Sub)):
                    if isinstance(arg.right, ast.Constant) and arg.right.value == 1:
                        patterns.add("off_by_one_risk")

    if has_direct_subscript and not has_empty_guard:
        patterns.add("unhandled_empty_input_risk")

    return patterns


def classify_attempt_mistake(
    attempt: dict[str, Any],
    challenge: dict[str, Any] | None,
) -> str | None:
    if attempt.get("passed"):
        return None

    results = attempt.get("test_results", [])
    categories = {r.get("category") for r in results}

    if "timeout" in categories:
        return "unbounded_loop"

    code = attempt.get("submitted_code", "")
    code_risks = _analyze_code_patterns(code)

    # Check test-case level clues
    visible_tests = challenge.get("visible_tests", []) if challenge else []
    for index, res in enumerate(results):
        category = res.get("category")
        if category in ("runtime error", "wrong output"):
            if index < len(visible_tests):
                case = visible_tests[index]
                args = case.get("input", [])
                # Was this test case checking empty string or empty list or 0?
                if any(arg in ("", [], [[]], 0) for arg in args):
                    return "unhandled_empty_input"

    # If code accesses subscript without guard and failed
    if "unhandled_empty_input_risk" in code_risks and ("runtime error" in categories or "wrong output" in categories):
        return "unhandled_empty_input"

    # Off-by-one indicator
    if "off_by_one_risk" in code_risks or "wrong output" in categories:
        # Check if wrong output might be off-by-one
        return "off_by_one"

    if "runtime error" in categories:
        return "unhandled_empty_input"

    return None


from hashlib import sha256


def _fingerprint(attempt: dict[str, Any]) -> str:
    code = attempt.get("submitted_code", "")
    try:
        normalized = ast.dump(ast.parse(code), include_attributes=False)
    except (SyntaxError, ValueError):
        normalized = "\n".join(line.rstrip() for line in code.splitlines()).strip()
    return sha256(f"{attempt.get('challenge_id', '')}\n{normalized}".encode()).hexdigest()


def detect_recurring_mistakes(
    attempts: list[dict[str, Any]],
    challenges_by_id: dict[str, dict[str, Any]],
) -> list[RecurringMistake]:
    """Detect mistake patterns occurring across 2+ distinct attempts."""
    # Deduplicate identical code attempts
    seen_fingerprints: set[str] = set()
    unique_attempts: list[dict[str, Any]] = []
    for att in attempts:
        fp = _fingerprint(att)
        if fp not in seen_fingerprints:
            seen_fingerprints.add(fp)
            unique_attempts.append(att)

    mistake_counts: dict[str, list[dict[str, Any]]] = {
        "unhandled_empty_input": [],
        "off_by_one": [],
        "type_mismatch": [],
        "unbounded_loop": [],
    }

    for attempt in unique_attempts:
        ch_id = attempt.get("challenge_id", "")
        challenge = challenges_by_id.get(ch_id)
        mistake = classify_attempt_mistake(attempt, challenge)
        if mistake and mistake in mistake_counts:
            mistake_counts[mistake].append(attempt)

    recurring: list[RecurringMistake] = []

    if len(mistake_counts["unhandled_empty_input"]) >= 2:
        affected = sorted({a["challenge_id"] for a in mistake_counts["unhandled_empty_input"]})
        recurring.append(RecurringMistake(
            mistake_type="unhandled_empty_input",
            label="Unhandled Empty Inputs",
            description="Code failed on empty strings, empty lists, or missing edge guards.",
            occurrences=len(mistake_counts["unhandled_empty_input"]),
            affected_challenges=affected,
            focus_advice="Add an early check like 'if not input_val: return ...' at the start of your function to handle empty inputs safely.",
        ))

    if len(mistake_counts["off_by_one"]) >= 2:
        affected = sorted({a["challenge_id"] for a in mistake_counts["off_by_one"]})
        recurring.append(RecurringMistake(
            mistake_type="off_by_one",
            label="Off-by-One Boundary Errors",
            description="Results differed by 1 element or boundary condition in loops/slices.",
            occurrences=len(mistake_counts["off_by_one"]),
            affected_challenges=affected,
            focus_advice="Double check slice endpoints and loop boundaries: Python 0-indexed sequences end at len - 1.",
        ))

    if len(mistake_counts["unbounded_loop"]) >= 2:
        affected = sorted({a["challenge_id"] for a in mistake_counts["unbounded_loop"]})
        recurring.append(RecurringMistake(
            mistake_type="unbounded_loop",
            label="Unbounded Loop / Timeout",
            description="Repeated timeouts indicate loop conditions not reaching termination.",
            occurrences=len(mistake_counts["unbounded_loop"]),
            affected_challenges=affected,
            focus_advice="Verify loop step increments and termination conditions before running tests.",
        ))

    return recurring


MISTAKE_CONCEPTS: dict[str, set[str]] = {
    "unhandled_empty_input": {"strings", "lists", "conditionals"},
    "off_by_one": {"loops", "slicing", "lists", "strings"},
    "type_mismatch": {"conditionals", "modulo", "functions", "booleans"},
    "unbounded_loop": {"loops"},
}


def adapt_recommendations_for_mistakes(
    recurring_mistakes: list[RecurringMistake],
    challenges: list[dict[str, Any]],
    solved_ids: set[str],
) -> list[PracticeRecommendation]:
    """Generate high-priority recommendations tailored to detected recurring mistakes."""
    diff_rank = {"beginner": 0, "easy": 1, "medium": 2, "hard": 3, "advanced": 4}
    adapted: list[PracticeRecommendation] = []

    for mistake in recurring_mistakes:
        target_tags = MISTAKE_CONCEPTS.get(mistake.mistake_type, set())
        matching = [
            c for c in challenges
            if any(t in target_tags for t in c.get("concept_tags", []))
        ]
        candidates = matching if matching else challenges

        # Prioritize unsolved, simplest difficulty
        sorted_candidates = sorted(
            candidates,
            key=lambda ch: (
                ch["id"] in solved_ids,
                diff_rank.get(ch.get("difficulty", "medium"), 2),
                ch.get("title", ""),
            ),
        )

        if sorted_candidates:
            chosen = sorted_candidates[0]
            # Match the first relevant tag or first concept tag
            matching_tags = [t for t in chosen.get("concept_tags", []) if t in target_tags]
            concept = matching_tags[0] if matching_tags else (chosen.get("concept_tags", ["logic"])[0])
            adapted.append(PracticeRecommendation(
                concept=concept,
                repeated_category=mistake.label,
                challenge_id=chosen["id"],
                challenge_title=chosen["title"],
                reason=(
                    f"Adapted for your learning path: {mistake.label} was detected across {mistake.occurrences} attempts "
                    f"in {', '.join(mistake.affected_challenges)}. Practice {chosen['title']} ({chosen['difficulty']}) "
                    f"to master: {mistake.focus_advice}"
                ),
                adapted_for=mistake.mistake_type,
            ))

    return adapted


def get_demonstrated_skills_for_concept(
    concept: str,
    solved_challenges: set[str],
) -> list[str]:
    """Return specific demonstrated skills for a concept based on solved challenges."""
    skills = set()
    for ch_id in solved_challenges:
        ch_skills = SKILLS_BY_CHALLENGE.get(ch_id, {})
        if concept in ch_skills:
            skills.update(ch_skills[concept])
    return sorted(skills)
