import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("CODEQUEST_STORAGE", "local")

from fastapi.testclient import TestClient  # noqa: E402

from app.local_repository import LocalRepository  # noqa: E402
from app.main import app  # noqa: E402
from app.repository import get_repository  # noqa: E402


class LocalRepositoryTests(unittest.TestCase):
    def test_six_challenges_progress_and_hidden_tests(self):
        path = Path(__file__).parent / "demo-test.sqlite3"
        try:
            repository = LocalRepository(path)
            app.dependency_overrides[get_repository] = lambda: repository
            try:
                client = TestClient(app)
                listing = client.get("/api/challenges")
                self.assertEqual(listing.status_code, 200)
                self.assertEqual(len(listing.json()), 6)
                detail = client.get("/api/challenges/add-numbers")
                self.assertEqual(detail.status_code, 200)
                self.assertNotIn("hidden_tests", detail.text)
                self.assertNotIn("-13", detail.text)
                list_detail = client.get("/api/challenges/sum-list")
                self.assertEqual(list_detail.status_code, 200)
                self.assertEqual(list_detail.json()["visible_tests"][0]["input"], [[1, 2, 3]])
                hints = [client.post("/api/challenges/add-numbers/hints/next", json={}).json() for _ in range(4)]
                self.assertEqual([hint["hint_number"] for hint in hints], [1, 2, 3, 3])
                self.assertTrue(all(hint["hint"] for hint in hints[:3]))
                self.assertIsNone(hints[3]["hint"])
                progress = client.get("/api/learners/demo-learner/progress")
                self.assertEqual(progress.json()["total_attempts"], 0)
                self.assertIn("lists", [item["concept"] for item in progress.json()["concepts"]])
                with patch("app.runner.subprocess.run", side_effect=FileNotFoundError):
                    run = client.post(
                        "/api/challenges/add-numbers/attempts",
                        json={"code": "def add_numbers(a, b):\n    return a + b"},
                    )
                self.assertEqual(run.status_code, 503)
                self.assertIn("Docker is unavailable", run.json()["detail"])
                self.assertEqual(repository.list_attempts("demo-learner"), [])

                for version in ("first version", "second version"):
                    repository.save_attempt({
                        "challenge_id": "count-vowels", "learner_id": "demo-learner",
                        "submitted_code": version, "passed": False,
                        "concepts_practiced": ["loops", "strings", "conditionals"],
                        "test_results": [{"name": "hidden-1", "visibility": "hidden", "category": "wrong output"}],
                    })
                updated_response = client.get("/api/learners/demo-learner/progress")
                self.assertNotIn("submitted_code", updated_response.text)
                self.assertNotIn("hidden-1", updated_response.text)
                updated = updated_response.json()
                self.assertEqual(updated["total_attempts"], 2)
                loops = next(item for item in updated["concepts"] if item["concept"] == "loops")
                self.assertEqual(loops["status"], "practicing")
                self.assertEqual(loops["recent_results"], ["wrong output", "wrong output"])
                suggestion = next(item for item in updated["recommendations"] if item["concept"] == "loops")
                self.assertEqual(suggestion["challenge_id"], "sum-list")
            finally:
                app.dependency_overrides.clear()
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
