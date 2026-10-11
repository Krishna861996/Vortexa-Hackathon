"""Execute Python tests through a sandboxed Piston service."""

import concurrent.futures
import json
import subprocess
import time
import urllib.error
import urllib.request
from uuid import uuid4
from typing import Any

from .models import TestResult


IMAGE = "codequest-python-runner:local"
TEST_TIMEOUT_SECONDS = 4
SETUP_TIMEOUT_SECONDS = 3
MAX_RUNNER_OUTPUT_BYTES = 8192


class RunnerUnavailable(Exception):
    pass


class PistonRunner:
    """Piston keeps untrusted execution outside the API process."""
    def __init__(self, base_url: str = "https://emkc.org/api/v2/piston", token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _execute(self, code: str, function_name: str, arguments: list[Any]) -> tuple[str, Any]:
        harness = (
            code + "\n\n" +
            "import json\n" +
            f"_args = json.loads({json.dumps(json.dumps(arguments))!r})\n" +
            f"_result = {function_name}(*_args)\n" +
            "print('__CODEQUEST_RESULT__' + json.dumps(_result))\n"
        )
        body = json.dumps({
            "language": "python", "version": "3.10.0",
            "files": [{"name": "main.py", "content": harness}],
            "stdin": "", "args": [], "compile_timeout": 3000,
            "run_timeout": int(TEST_TIMEOUT_SECONDS * 1000),
        }).encode()
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token if self.token.lower().startswith("bearer ") else f"Bearer {self.token}"
        request = urllib.request.Request(f"{self.base_url}/execute", data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=SETUP_TIMEOUT_SECONDS + TEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read(MAX_RUNNER_OUTPUT_BYTES * 2))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise RunnerUnavailable("Piston is unavailable. Set PISTON_URL and PISTON_TOKEN, or run a local Piston instance.") from exc
        run = payload.get("run") or {}
        if run.get("signal") or run.get("code") in (124, 137):
            return "timeout", None
        if run.get("code", 0) != 0:
            return "runtime error", None
        marker = "__CODEQUEST_RESULT__"
        output = run.get("output", "")
        line = next((line for line in output.splitlines() if line.startswith(marker)), None)
        if line is None:
            return "runtime error", None
        try:
            return "ok", json.loads(line[len(marker):])
        except json.JSONDecodeError:
            return "runtime error", None

    def grade(self, challenge: dict[str, Any], code: str, hidden_tests: list[dict[str, Any]]) -> list[TestResult]:
        cases = [("visible", case) for case in challenge["visible_tests"]]
        cases.extend(("hidden", case) for case in hidden_tests)
        counts = {"visible": 0, "hidden": 0}
        results = []
        for visibility, case in cases:
            counts[visibility] += 1
            status, actual = self._execute(code, challenge["function_name"], case["input"])
            category = status if status != "ok" else ("passed" if type(actual) is type(case["expected"]) and actual == case["expected"] else "wrong output")
            results.append(TestResult(name=f"{visibility}-{counts[visibility]}", visibility=visibility, category=category))
        return results


class DockerRunner:
    def __init__(self, image: str = IMAGE):
        self.image = image

    def check_ready(self) -> None:
        try:
            info = subprocess.run(
                ["docker", "info", "--format", "{{.OSType}}"],
                capture_output=True, text=True, timeout=SETUP_TIMEOUT_SECONDS, check=False,
            )
            if info.returncode != 0 or info.stdout.strip() != "linux":
                raise RunnerUnavailable("A running Docker Linux daemon is required for Python submissions.")
            image = subprocess.run(
                ["docker", "image", "inspect", self.image, "--format", "{{.Id}}"],
                capture_output=True, text=True, timeout=SETUP_TIMEOUT_SECONDS, check=False,
            )
            if image.returncode != 0 or not image.stdout.strip():
                raise RunnerUnavailable(
                    "The CodeQuest runner image is missing. Build it with: "
                    "docker build -t codequest-python-runner:local backend/runner"
                )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
            raise RunnerUnavailable("Docker is unavailable. Install and start Docker with Linux containers enabled.") from exc

    @staticmethod
    def command(name: str, image: str) -> list[str]:
        return [
            "docker", "run", "--rm", "--interactive", "--pull=never",
            "--name", name, "--network=none", "--read-only",
            "--user=65534:65534", "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true",
            "--security-opt=seccomp=builtin", "--pids-limit=32",
            "--memory=128m", "--memory-swap=128m", "--cpus=0.5",
            "--ipc=none", "--log-driver=none", "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
            "--ulimit=nofile=64:64", image,
        ]

    @staticmethod
    def cleanup(name: str) -> None:
        try:
            result = subprocess.run(
                ["docker", "rm", "--force", name],
                capture_output=True,
                timeout=SETUP_TIMEOUT_SECONDS, check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
            raise RunnerUnavailable("Docker could not stop a timed-out runner container.") from exc
        if result.returncode != 0 and b"No such container" not in result.stderr:
            raise RunnerUnavailable("Docker could not stop a timed-out runner container.")

    def run_test(self, code: str, function_name: str, arguments: list[Any]) -> tuple[str, Any]:
        name = f"codequest-{uuid4().hex}"
        payload = json.dumps({"code": code, "function_name": function_name, "input": arguments}).encode()
        command = self.command(name, self.image)
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except (FileNotFoundError, OSError) as exc:
            raise RunnerUnavailable("Docker is unavailable. Install and start Docker with Linux containers enabled.") from exc

        should_cleanup = False
        deadline = time.monotonic() + TEST_TIMEOUT_SECONDS
        try:
            if process.stdin is None or process.stdout is None:
                raise RunnerUnavailable("Docker runner pipes could not be opened.")
            try:
                process.stdin.write(payload)
                process.stdin.close()
            except OSError:
                pass

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                output_future = pool.submit(process.stdout.read, MAX_RUNNER_OUTPUT_BYTES + 1)
                try:
                    output = output_future.result(timeout=max(0, deadline - time.monotonic()))
                except concurrent.futures.TimeoutError:
                    process.kill()
                    should_cleanup = True
                    return "timeout", None

            if len(output) > MAX_RUNNER_OUTPUT_BYTES:
                process.kill()
                should_cleanup = True
                return "runtime error", None
            try:
                returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                process.kill()
                should_cleanup = True
                return "timeout", None
            if returncode in (125, 126, 127):
                raise RunnerUnavailable("Docker could not start the restricted runner container. Check Docker setup and image.")
            if returncode != 0:
                return "runtime error", None
            try:
                result = json.loads(output)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return "runtime error", None
            if result == {"status": "runtime_error"}:
                return "runtime error", None
            if isinstance(result, dict) and set(result) == {"status", "value"} and result["status"] == "ok":
                return "ok", result["value"]
            return "runtime error", None
        finally:
            wait_failed = False
            try:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                wait_failed = True
            if should_cleanup or wait_failed:
                self.cleanup(name)
            if wait_failed:
                raise RunnerUnavailable("Docker runner process did not stop after its deadline.")

    def grade(self, challenge: dict[str, Any], code: str, hidden_tests: list[dict[str, Any]]) -> list[TestResult]:
        self.check_ready()
        cases = [("visible", case) for case in challenge["visible_tests"]]
        cases.extend(("hidden", case) for case in hidden_tests)
        results = []
        counts = {"visible": 0, "hidden": 0}
        for visibility, case in cases:
            counts[visibility] += 1
            status, actual = self.run_test(code, challenge["function_name"], case["input"])
            if status == "ok":
                expected = case["expected"]
                category = "passed" if type(actual) is type(expected) and actual == expected else "wrong output"
            else:
                category = status
            results.append(TestResult(
                name=f"{visibility}-{counts[visibility]}",
                visibility=visibility, category=category,
            ))
        return results


def get_runner() -> DockerRunner:
    from .config import get_settings
    settings = get_settings()
    if settings.codequest_runner == "docker":
        return DockerRunner()
    return PistonRunner(settings.piston_url, settings.piston_token)
