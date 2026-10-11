import io
import threading
import unittest
from unittest.mock import patch

from app.runner import DockerRunner, RunnerUnavailable


class FakeProcess:
    def __init__(self, output: bytes, returncode: int = 0):
        self.stdin = CapturingInput()
        self.stdout = io.BytesIO(output)
        self.returncode = returncode
        self.killed = False

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class CapturingInput(io.BytesIO):
    def close(self):
        self.sent = self.getvalue()
        super().close()


class BlockingOutput:
    def __init__(self):
        self.stopped = threading.Event()

    def read(self, count):
        self.stopped.wait()
        return b""


class RunnerTests(unittest.TestCase):
    def test_command_enforces_isolation(self):
        command = DockerRunner.command("codequest-test", "codequest-python-runner:local")
        for flag in (
            "--network=none", "--read-only", "--user=65534:65534",
            "--cap-drop=ALL", "--security-opt=no-new-privileges=true",
            "--security-opt=seccomp=builtin", "--memory=128m",
            "--cpus=0.5", "--pids-limit=32", "--pull=never",
        ):
            self.assertIn(flag, command)

    def test_submission_payload_does_not_include_expected_value(self):
        process = FakeProcess(b'{"status":"ok","value":5}')
        with patch("app.runner.subprocess.Popen", return_value=process) as popen:
            status, value = DockerRunner().run_test("def add_numbers(a, b): return a + b", "add_numbers", [2, 3])
        self.assertEqual((status, value), ("ok", 5))
        self.assertNotIn("def add_numbers", " ".join(popen.call_args.args[0]))
        self.assertNotIn(b"expected", process.stdin.sent)

    def test_four_result_categories(self):
        challenge = {"function_name": "add_numbers", "visible_tests": [
            {"input": [2, 3], "expected": 5},
            {"input": [2, 3], "expected": 5},
            {"input": [2, 3], "expected": 5},
        ]}
        hidden = [{"input": [99, 1], "expected": 100}]
        runner = DockerRunner()
        with patch.object(runner, "check_ready"), patch.object(runner, "run_test", side_effect=[
            ("ok", 5), ("ok", 7), ("runtime error", None), ("timeout", None),
        ]):
            results = runner.grade(challenge, "def add_numbers(a, b): return a + b", hidden)
        self.assertEqual([item.category for item in results], [
            "passed", "wrong output", "runtime error", "timeout",
        ])
        self.assertEqual(results[-1].model_dump(), {
            "name": "hidden-1", "visibility": "hidden", "category": "timeout", "execution": "server",
        })

    def test_missing_docker_fails_closed(self):
        with patch("app.runner.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RunnerUnavailable, "Docker is unavailable"):
                DockerRunner().check_ready()

    def test_strict_timeout_kills_and_removes_container(self):
        process = FakeProcess(b"", returncode=None)
        process.stdout = BlockingOutput()
        original_kill = process.kill

        def kill():
            original_kill()
            process.stdout.stopped.set()

        process.kill = kill
        with patch("app.runner.TEST_TIMEOUT_SECONDS", 0.02), \
             patch("app.runner.subprocess.Popen", return_value=process), \
             patch.object(DockerRunner, "cleanup") as cleanup:
            status, _ = DockerRunner().run_test("while True: pass", "add_numbers", [2, 3])
        self.assertEqual(status, "timeout")
        self.assertTrue(process.killed)
        cleanup.assert_called_once()

    def test_docker_start_error_is_setup_error(self):
        process = FakeProcess(b"", returncode=125)
        with patch("app.runner.subprocess.Popen", return_value=process):
            with self.assertRaisesRegex(RunnerUnavailable, "could not start"):
                DockerRunner().run_test("pass", "add_numbers", [2, 3])


if __name__ == "__main__":
    unittest.main()
