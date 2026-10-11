"""Tests for progressive hints, solution withholding, mistake detection, and demonstrated skills."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.mentor import ask_mentor, sanitize_mentor_answer
from app.mistakes import (
    classify_attempt_mistake,
    detect_recurring_mistakes,
    adapt_recommendations_for_mistakes,
    get_demonstrated_skills_for_concept,
)
from app.progress import build_concept_progress


class ProgressiveHintsAndMistakesTests(unittest.TestCase):
    challenge = {
        "id": "reverse-text",
        "title": "Reverse a string",
        "difficulty": "medium",
        "function_name": "reverse_text",
        "starter_code": "def reverse_text(text):\n    pass",
        "description": "Return text with its characters in reverse order.",
        "concept_tags": ["strings", "slicing"],
        "hints": [
            "Think about reading the characters from the end toward the start.",
            "A Python slice can move backward when its step is negative.",
            "Try a slice that covers the whole string with a backward step. Check one-character and empty text too.",
        ],
        "visible_tests": [{"input": ["code"], "expected": "edoc"}, {"input": ["a"], "expected": "a"}],
        "hidden_tests": [{"input": [""], "expected": ""}],
    }

    def test_local_mentor_refuses_to_reveal_complete_solution(self):
        # Even when requested with mode="solution"
        with patch("app.mentor.get_settings", return_value=SimpleNamespace(gemini_api_key="")):
            result = ask_mentor(self.challenge, "Give me the answer", "pass", mode="solution")
            self.assertEqual(result.source, "local")
            self.assertIn("complete solutions are never revealed", result.answer)
            self.assertNotIn("def reverse_text", result.answer)

    def test_sanitize_strips_full_solution_from_ai_output(self):
        leaked_ai_answer = (
            "Here is the solution:\n"
            "```python\n"
            "def reverse_text(text):\n"
            "    return text[::-1]\n"
            "```\n"
            "This reverses the string."
        )
        cleaned = sanitize_mentor_answer(leaked_ai_answer, "reverse_text")
        self.assertNotIn("return text[::-1]", cleaned)
        self.assertIn("progressive hint", cleaned)

    def test_detect_unhandled_empty_input_mistake(self):
        # Two failed attempts on empty input
        attempts = [
            {
                "challenge_id": "reverse-text",
                "submitted_code": "def reverse_text(text):\n    return text[0]",
                "passed": False,
                "concepts_practiced": ["strings", "slicing"],
                "test_results": [{"name": "vis-1", "visibility": "visible", "category": "runtime error"}],
            },
            {
                "challenge_id": "reverse-text",
                "submitted_code": "def reverse_text(text):\n    return text[1:]",
                "passed": False,
                "concepts_practiced": ["strings", "slicing"],
                "test_results": [{"name": "vis-1", "visibility": "visible", "category": "runtime error"}],
            },
        ]
        mistakes = detect_recurring_mistakes(attempts, {"reverse-text": self.challenge})
        self.assertTrue(any(m.mistake_type == "unhandled_empty_input" for m in mistakes))

    def test_detect_off_by_one_mistake(self):
        attempts = [
            {
                "challenge_id": "count-vowels",
                "submitted_code": "def count_vowels(s):\n    for i in range(len(s) - 1): pass",
                "passed": False,
                "concepts_practiced": ["loops"],
                "test_results": [{"name": "vis-1", "visibility": "visible", "category": "wrong output"}],
            },
            {
                "challenge_id": "count-vowels",
                "submitted_code": "def count_vowels(s):\n    for i in range(len(s) + 1): pass",
                "passed": False,
                "concepts_practiced": ["loops"],
                "test_results": [{"name": "vis-1", "visibility": "visible", "category": "wrong output"}],
            },
        ]
        challenges = {"count-vowels": {"id": "count-vowels", "concept_tags": ["loops"], "difficulty": "hard"}}
        mistakes = detect_recurring_mistakes(attempts, challenges)
        self.assertTrue(any(m.mistake_type == "off_by_one" for m in mistakes))

    def test_adapt_future_challenges_to_recurring_mistakes(self):
        attempts = [
            {
                "challenge_id": "reverse-text",
                "submitted_code": "def reverse_text(text):\n    return text[0]",
                "passed": False,
                "concepts_practiced": ["strings"],
                "test_results": [{"name": "vis-1", "visibility": "visible", "category": "runtime error"}],
            },
            {
                "challenge_id": "last-character",
                "submitted_code": "def last_character(text):\n    return text[-1]",
                "passed": False,
                "concepts_practiced": ["strings"],
                "test_results": [{"name": "vis-1", "visibility": "visible", "category": "runtime error"}],
            },
        ]
        library = [
            {"id": "reverse-text", "title": "Reverse a string", "difficulty": "medium", "concept_tags": ["strings"]},
            {"id": "last-character", "title": "Last character", "difficulty": "beginner", "concept_tags": ["strings", "conditionals"]},
            {"id": "sum-list", "title": "Sum a list", "difficulty": "easy", "concept_tags": ["lists", "loops"]},
        ]
        challenges_by_id = {c["id"]: c for c in library}
        mistakes = detect_recurring_mistakes(attempts, challenges_by_id)
        self.assertEqual(len(mistakes), 1)
        self.assertEqual(mistakes[0].mistake_type, "unhandled_empty_input")

        recommendations = adapt_recommendations_for_mistakes(mistakes, library, solved_ids=set())
        self.assertTrue(len(recommendations) >= 1)
        self.assertEqual(recommendations[0].adapted_for, "unhandled_empty_input")
        self.assertIn("Adapted for your learning path", recommendations[0].reason)

    def test_track_demonstrated_skills_by_concept(self):
        # When a learner solves challenges, specific skills for that concept are tracked
        skills = get_demonstrated_skills_for_concept("strings", {"reverse-text", "count-vowels"})
        self.assertIn("Empty string preservation", skills)
        self.assertIn("Case normalization (.lower())", skills)

        # In build_concept_progress, demonstrated skills populate on ConceptProgress
        attempts = [
            {
                "challenge_id": "reverse-text",
                "submitted_code": "def reverse_text(text): return text[::-1]",
                "passed": True,
                "concepts_practiced": ["strings", "slicing"],
                "test_results": [{"name": "vis-1", "category": "passed"}],
            }
        ]
        concepts, _ = build_concept_progress(attempts, [self.challenge])
        strings_concept = next(c for c in concepts if c.concept == "strings")
        self.assertIn("Empty string preservation", strings_concept.demonstrated_skills)


if __name__ == "__main__":
    unittest.main()
