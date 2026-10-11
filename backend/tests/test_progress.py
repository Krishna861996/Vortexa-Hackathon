import unittest

from app.progress import build_concept_progress


CHALLENGES = [
    {"id": "sum-list", "title": "Sum a list", "difficulty": "easy", "concept_tags": ["lists", "loops"]},
    {"id": "count-vowels", "title": "Count vowels", "difficulty": "hard", "concept_tags": ["loops", "strings"]},
]


def attempt(code, passed, category, challenge_id="count-vowels"):
    return {
        "challenge_id": challenge_id, "passed": passed,
        "concepts_practiced": ["loops", "strings"] if challenge_id == "count-vowels" else ["lists", "loops"],
        "submitted_code": code,
        "test_results": [{"name": "hidden-1", "visibility": "hidden", "category": category}],
    }


class ProgressRulesTests(unittest.TestCase):
    def test_repeated_failure_recommends_simpler_related_challenge(self):
        attempts = [attempt("version 2", False, "wrong output"), attempt("version 1", False, "wrong output")]
        concepts, recommendations = build_concept_progress(attempts, CHALLENGES)
        loops = next(item for item in concepts if item.concept == "loops")
        self.assertEqual(loops.status, "practicing")
        self.assertEqual(loops.recent_results, ["wrong output", "wrong output"])
        recommendation = next(item for item in recommendations if item.concept == "loops")
        self.assertEqual(recommendation.challenge_id, "sum-list")
        self.assertIn("two latest attempts with different code", recommendation.reason)
        self.assertNotIn("hidden", recommendation.reason)

        attempts[0]["submitted_code"] = "version 1"
        _, recommendations = build_concept_progress(attempts, CHALLENGES)
        self.assertEqual(recommendations, [])

    def test_demonstrated_requires_distinct_repeated_success(self):
        attempts = [
            attempt("solution b", True, "passed"),
            attempt("solution a", True, "passed"),
            attempt("first try", False, "wrong output"),
        ]
        concepts, recommendations = build_concept_progress(attempts, CHALLENGES)
        loops = next(item for item in concepts if item.concept == "loops")
        self.assertEqual(loops.status, "demonstrated")
        self.assertEqual(loops.distinct_passing_solutions, 2)
        self.assertEqual(recommendations, [])

        attempts[0]["submitted_code"] = "solution a"
        concepts, _ = build_concept_progress(attempts, CHALLENGES)
        self.assertEqual(next(item for item in concepts if item.concept == "loops").status, "improving")

        attempts[0]["submitted_code"] = "def solve():\n    return 1  # a comment"
        attempts[1]["submitted_code"] = "def solve():\n  return 1"
        concepts, _ = build_concept_progress(attempts, CHALLENGES)
        self.assertEqual(next(item for item in concepts if item.concept == "loops").distinct_passing_solutions, 1)

    def test_no_attempts_are_not_started_and_one_pass_is_practicing(self):
        concepts, _ = build_concept_progress([], CHALLENGES)
        self.assertTrue(all(item.status == "not started" for item in concepts))
        concepts, _ = build_concept_progress([attempt("solution", True, "passed")], CHALLENGES)
        self.assertEqual(next(item for item in concepts if item.concept == "loops").status, "practicing")
        concepts, _ = build_concept_progress(
            [attempt("new failure", False, "wrong output"), attempt("old success", True, "passed")],
            CHALLENGES,
        )
        self.assertEqual(next(item for item in concepts if item.concept == "loops").status, "practicing")
