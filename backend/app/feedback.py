"""Deterministic, non-diagnostic guidance for failed submissions.

Only result categories and public challenge concepts are used. Hidden test
inputs, expected outputs, and submitted code never enter this function.
"""

from .models import TestResult


WRONG_OUTPUT_TIPS = {
    "arithmetic": "Check how both arguments are combined, including zero and negative values.",
    "modulo": "Check the remainder condition and the value returned for each branch.",
    "slicing": "Check the direction of your slice and what happens with short text.",
    "loops": "Check whether every character is considered once, including uppercase letters.",
    "conditionals": "Check the order of your conditions when more than one could match.",
    "strings": "Check the text you return, including letter case and empty text.",
    "booleans": "Check that the function returns a boolean for both true and false cases.",
    "functions": "Check that the function returns the computed value instead of printing it.",
}


def explain_failure(concepts: list[str], results: list[TestResult]) -> str | None:
    categories = {result.category for result in results}
    if categories <= {"passed"}:
        return None

    if "timeout" in categories:
        if "loops" in concepts:
            return "A test ran out of time. A loop may not be reaching its stopping point. Check how its state changes on each pass, then try again."
        return "A test ran out of time. Check for repeated work or a call that never finishes, then try again."

    if "runtime error" in categories:
        if "slicing" in concepts or "strings" in concepts:
            return "Your code stopped while running. Check that string operations work for short or empty text and that the function returns a value."
        if "loops" in concepts:
            return "Your code stopped while running. Check the values used inside the loop and that the function returns after the loop."
        return "Your code stopped while running. Check the function name, parameters, and operations on the inputs before trying again."

    for concept in ("arithmetic", "slicing", "loops", "conditionals", "modulo", "strings", "booleans", "functions"):
        if concept in concepts:
            return f"Your code ran, but at least one result was different. {WRONG_OUTPUT_TIPS[concept]}"
    return "Your code ran, but at least one result was different. Compare your logic with the visible examples, then try another case."
