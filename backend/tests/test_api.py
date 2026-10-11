import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "test-only")

from app.main import get_challenge, get_progress, next_hint, submit_code  # noqa: E402
from app.main import app  # noqa: E402
from app.models import HintRequest, Submission  # noqa: E402
from app.repository import get_repository  # noqa: E402
from app.runner import get_runner  # noqa: E402
from app.models import TestResult  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class FakeRepository:
    def __init__(self):
        self.challenge = {
            "id": "add-numbers", "title": "Add two numbers", "description": "Return the sum.",
            "difficulty": "beginner", "function_name": "add_numbers",
            "starter_code": "def add_numbers(a, b):\n    pass",
            "visible_tests": [{"input": [2, 3], "expected": 5}],
            "hints": ["Use +", "Return a + b"], "concept_tags": ["arithmetic"],
        }
        self.learner = {"id": "demo-learner", "hint_positions": {}}
        self.attempts = []

    def get_challenge(self, challenge_id):
        return self.challenge if challenge_id == "add-numbers" else None

    def list_challenges(self):
        return [{key: self.challenge[key] for key in ("id", "title", "difficulty", "concept_tags")}]

    def get_hidden_tests(self, challenge_id):
        return [{"input": [99, 1], "expected": 100}]

    def get_learner(self, learner_id):
        return self.learner if learner_id == "demo-learner" else None

    def update_hint_positions(self, learner_id, positions):
        self.learner["hint_positions"] = positions

    def save_attempt(self, attempt):
        self.attempts.append(attempt)
        return {"id": len(self.attempts), "submitted_at": "2026-10-11T00:00:00+00:00"}

    def list_attempts(self, learner_id):
        return [
            {"challenge_id": item["challenge_id"], "passed": item["passed"],
             "concepts_practiced": item["concepts_practiced"],
             "submitted_at": "2026-10-11T00:00:00+00:00"}
            for item in reversed(self.attempts)
        ]


class FakeRunner:
    def grade(self, challenge, code, hidden_tests):
        category = "passed" if "a + b" in code else "wrong output"
        return [
            TestResult(name="visible-1", visibility="visible", category="passed"),
            TestResult(name="hidden-1", visibility="hidden", category=category),
        ]


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.repository = FakeRepository()

    def test_detail_excludes_hidden_tests_and_unrequested_hints(self):
        detail = get_challenge("add-numbers", self.repository).model_dump()
        self.assertNotIn("hidden_tests", detail)
        self.assertNotIn("hints", detail)
        self.assertEqual(detail["hint_count"], 2)

    def test_hint_sequence(self):
        first = next_hint("add-numbers", HintRequest(), self.repository)
        second = next_hint("add-numbers", HintRequest(), self.repository)
        third = next_hint("add-numbers", HintRequest(), self.repository)
        self.assertEqual((first.hint, second.hint, third.hint), ("Use +", "Return a + b", None))

    def test_submission_and_progress(self):
        attempt = submit_code("add-numbers", Submission(code="def add_numbers(a, b):\n    return a + b"), self.repository, FakeRunner())
        self.assertTrue(attempt.passed)
        self.assertEqual(self.repository.attempts[0]["submitted_code"], "def add_numbers(a, b):\n    return a + b")
        self.assertNotIn("input", attempt.model_dump_json())
        progress = get_progress("demo-learner", self.repository)
        self.assertEqual(progress.total_attempts, 1)
        self.assertEqual(progress.solved_challenges, 1)

    def test_http_detail_and_submission_hide_private_values(self):
        app.dependency_overrides[get_repository] = lambda: self.repository
        app.dependency_overrides[get_runner] = FakeRunner
        try:
            client = TestClient(app)
            listing = client.get("/api/challenges")
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(len(listing.json()), 1)
            detail = client.get("/api/challenges/add-numbers")
            self.assertEqual(detail.status_code, 200)
            self.assertNotIn("hidden_tests", detail.json())
            response = client.post(
                "/api/challenges/add-numbers/attempts",
                json={"code": "def add_numbers(a, b):\n    return 5"},
            )
            self.assertEqual(response.status_code, 200)
            hidden = response.json()["results"][1]
            self.assertEqual(hidden["category"], "wrong output")
            self.assertEqual(response.json()["feedback_source"], "local")
            self.assertIn("both arguments", response.json()["failure_explanation"])
            self.assertNotIn("actual", hidden)
            self.assertNotIn("message", hidden)
            self.assertNotIn("99", response.text)
            hint = client.post("/api/challenges/add-numbers/hints/next", json={})
            self.assertEqual(hint.json()["hint_number"], 1)
            progress = client.get("/api/learners/demo-learner/progress")
            self.assertEqual(progress.json()["total_attempts"], 1)
        finally:
            app.dependency_overrides.clear()

    def test_missing_docker_returns_setup_error_without_saving(self):
        app.dependency_overrides[get_repository] = lambda: self.repository
        try:
            with patch("app.runner.subprocess.run", side_effect=FileNotFoundError):
                response = TestClient(app).post(
                    "/api/challenges/add-numbers/attempts",
                    json={"code": "def add_numbers(a, b):\n    return a + b"},
                )
            self.assertEqual(response.status_code, 503)
            self.assertIn("Docker is unavailable", response.json()["detail"])
            self.assertEqual(self.repository.attempts, [])
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
