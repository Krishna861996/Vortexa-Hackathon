"""Intelligent code modification analyzer and explanation generator.

Detects code transformations (e.g. / to %, off-by-one fixes, return statements,
empty input guards) and provides clear educational explanations of what changed
and why the modification helps.
"""

import difflib
import re
from typing import Any


def analyze_code_diff(before_code: str, after_code: str, challenge: dict[str, Any] | None = None) -> dict[str, Any]:
    before_lines = before_code.splitlines()
    after_lines = after_code.splitlines()

    # Generate unified diff lines
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
    diff_hunks = []
    before_highlights = []
    after_highlights = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for idx, line in enumerate(before_lines[i1:i2]):
                diff_hunks.append({"type": "equal", "before_line": i1 + idx + 1, "after_line": j1 + idx + 1, "text": line})
        elif tag == "replace":
            for idx, line in enumerate(before_lines[i1:i2]):
                diff_hunks.append({"type": "removed", "before_line": i1 + idx + 1, "after_line": None, "text": line})
                before_highlights.append(i1 + idx + 1)
            for idx, line in enumerate(after_lines[j1:j2]):
                diff_hunks.append({"type": "added", "before_line": None, "after_line": j1 + idx + 1, "text": line})
                after_highlights.append(j1 + idx + 1)
        elif tag == "delete":
            for idx, line in enumerate(before_lines[i1:i2]):
                diff_hunks.append({"type": "removed", "before_line": i1 + idx + 1, "after_line": None, "text": line})
                before_highlights.append(i1 + idx + 1)
        elif tag == "insert":
            for idx, line in enumerate(after_lines[j1:j2]):
                diff_hunks.append({"type": "added", "before_line": None, "after_line": j1 + idx + 1, "text": line})
                after_highlights.append(j1 + idx + 1)

    explanations: list[str] = []
    why_it_helps: list[str] = []

    # Rule 1: Division (/) replaced by Modulo (%)
    if ("/" in before_code and "%" in after_code) and (re.search(r"/\s*2", before_code) and re.search(r"%\s*2", after_code)):
        explanations.append("`/` performs division (returning a quotient).")
        explanations.append("`%` calculates the remainder for integer operands.")
        explanations.append("The condition checks whether the remainder is zero.")
        why_it_helps.append("Divisibility and parity checks require checking if `n % 2 == 0`. Using `/` calculates `n / 2` which evaluates to a float or non-zero number instead of a remainder.")
    elif "/" in before_code and "%" in after_code:
        explanations.append("Replaced division operator `/` with remainder operator `%`.")
        why_it_helps.append("`%` computes the remainder of division, which is essential for modular arithmetic and factor checks.")

    # Rule 2: Single '=' replaced by '==' or vice versa
    if re.search(r"(?<!=)=(?!=)", before_code) and re.search(r"==", after_code):
        if any("==" in line for line in after_lines if any("=" in b for b in before_lines)):
            explanations.append("Replaced assignment `=` with comparison operator `==`.")
            why_it_helps.append("In Python, `=` assigns a value to a variable, while `==` checks whether two values are equal in conditional expressions.")

    # Rule 3: Added 'return' statement
    if "return " not in before_code and "return " in after_code:
        explanations.append("Added an explicit `return` statement.")
        why_it_helps.append("Without a `return` statement, Python functions implicitly return `None`. Returning the computed result allows tests to verify your function's output.")

    # Rule 4: Replaced 'print' with 'return'
    if "print(" in before_code and "return " in after_code and "print(" not in after_code:
        explanations.append("Replaced `print()` with `return`.")
        why_it_helps.append("`print()` writes text to the console display, but unit tests evaluate the value passed back via `return`.")

    # Rule 5: String slicing with step [::-1]
    if "[::-1]" not in before_code and "[::-1]" in after_code:
        explanations.append("Applied negative step slicing `[::-1]`.")
        why_it_helps.append("A slice with step `-1` traverses the sequence backwards from end to start, reversing string or list elements concisely.")

    # Rule 6: Off-by-one correction in range or index
    if re.search(r"range\(len\(.+?\)\)", before_code) and re.search(r"range\(len\(.+?\)\s*-\s*1\)", after_code):
        explanations.append("Adjusted loop bound from `range(len(...))` to `range(len(...) - 1)`.")
        why_it_helps.append("Prevents an `IndexError: string index out of range` when inspecting adjacent pairs (e.g. `s[i]` and `s[i+1]`).")
    elif ("<=" in before_code and "<" in after_code) or ("<" in before_code and "<=" in after_code):
        explanations.append("Adjusted comparison boundary operator (`<` vs `<=`).")
        why_it_helps.append("Boundary condition adjustments ensure the loop or check includes or excludes edge items accurately.")

    # Rule 7: Empty input handling (guard condition)
    if not re.search(r"if\s+not\s+|len\(.+?\)\s*==\s*0", before_code) and re.search(r"if\s+not\s+|len\(.+?\)\s*==\s*0", after_code):
        explanations.append("Added a guard condition for empty inputs.")
        why_it_helps.append("Handling empty sequences early prevents `IndexError` or unexpected defaults on zero-length arguments.")

    # Rule 8: .lower() or .upper() normalization
    if ".lower()" not in before_code and ".lower()" in after_code:
        explanations.append("Added `.lower()` case normalization.")
        why_it_helps.append("Converts characters to lowercase so comparisons match both uppercase and lowercase inputs consistently.")

    # Rule 9: Integer accumulator initialization
    if not re.search(r"\b(count|total|result|ans)\s*=\s*0\b", before_code) and re.search(r"\b(count|total|result|ans)\s*=\s*0\b", after_code):
        explanations.append("Initialized a running accumulator variable before the loop.")
        why_it_helps.append("Accumulating values in a loop requires starting from zero or a neutral identity element.")

    # Fallback explanation if no specific pattern was recognized
    if not explanations:
        added_count = len(after_highlights)
        removed_count = len(before_highlights)
        if added_count > 0 and removed_count > 0:
            explanations.append(f"Modified {removed_count} line(s) and added {added_count} new line(s).")
            why_it_helps.append("Refined the logic and expressions to better align with the required function signature and edge cases.")
        elif added_count > 0:
            explanations.append(f"Added {added_count} new line(s) of code.")
            why_it_helps.append("Introduced additional statements or helper logic to complete the function.")
        elif removed_count > 0:
            explanations.append(f"Removed {removed_count} line(s) of code.")
            why_it_helps.append("Simplified the implementation and eliminated redundant statements.")
        else:
            explanations.append("Minor whitespace or formatting adjustment.")
            why_it_helps.append("Clean formatting improves code clarity and readability.")

    return {
        "diff_hunks": diff_hunks,
        "before_highlights": before_highlights,
        "after_highlights": after_highlights,
        "explanations": explanations,
        "why_it_helps": why_it_helps,
    }
