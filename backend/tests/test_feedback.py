import unittest

from app.feedback import explain_failure
from app.models import TestResult


class FeedbackTests(unittest.TestCase):
    def test_categories_get_plain_language_without_private_values(self):
        for category, phrase in (
            ("wrong output", "remainder"),
            ("runtime error", "stopped while running"),
            ("timeout", "ran out of time"),
        ):
            with self.subTest(category=category):
                result = TestResult(name="hidden-1", visibility="hidden", category=category)
                feedback = explain_failure(["modulo", "booleans"], [result])
                self.assertIn(phrase, feedback)
                self.assertNotIn("hidden", feedback.lower())
                self.assertNotIn("AI", feedback)

    def test_passed_submission_has_no_failure_explanation(self):
        passed = TestResult(name="visible-1", visibility="visible", category="passed")
        self.assertIsNone(explain_failure(["functions"], [passed]))
