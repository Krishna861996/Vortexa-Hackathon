"""Real-container tests run after building the runner image; skipped without Docker."""

import unittest

from app.runner import DockerRunner, RunnerUnavailable


class DockerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = DockerRunner()
        try:
            cls.runner.check_ready()
        except RunnerUnavailable as exc:
            raise unittest.SkipTest(str(exc)) from exc

    def test_correct_incorrect_runtime_error_and_timeout(self):
        cases = [
            ("def add_numbers(a, b):\n    return a + b", "ok", 5),
            ("def add_numbers(a, b):\n    return a - b", "ok", -1),
            ("def add_numbers(a, b):\n    raise ValueError('bad')", "runtime error", None),
            ("def add_numbers(a, b):\n    while True:\n        pass", "timeout", None),
        ]
        for code, status, value in cases:
            with self.subTest(status=status, code=code):
                self.assertEqual(self.runner.run_test(code, "add_numbers", [2, 3]), (status, value))


if __name__ == "__main__":
    unittest.main()
