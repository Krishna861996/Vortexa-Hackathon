"""Container-only entry point. Receives one test input; never receives expected output."""

import json
import os
import sys


def execute(payload: dict) -> dict:
    # Preserve a protocol stream while suppressing all output from submitted code.
    protocol_fd = os.dup(1)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    original_stdout, original_stderr = sys.stdout, sys.stderr
    try:
        with open(os.devnull, "w", encoding="utf-8") as sink:
            sys.stdout = sink
            sys.stderr = sink
            os.dup2(null_fd, 1)
            os.dup2(null_fd, 2)
            try:
                scope = {"__name__": "__submission__"}
                exec(compile(payload["code"], "<submission>", "exec"), scope, scope)
                function = scope[payload["function_name"]]
                value = function(*payload["input"])
                encoded = json.dumps({"status": "ok", "value": value}, allow_nan=False)
                if len(encoded.encode()) > 4096:
                    return {"status": "runtime_error"}
                return {"status": "ok", "value": value}
            except BaseException:
                return {"status": "runtime_error"}
    finally:
        os.dup2(protocol_fd, 1)
        os.dup2(protocol_fd, 2)
        os.close(protocol_fd)
        os.close(null_fd)
        sys.stdout, sys.stderr = original_stdout, original_stderr


if __name__ == "__main__":
    try:
        raw = sys.stdin.buffer.read(8193)
        if len(raw) > 8192:
            raise ValueError("Payload too large")
        answer = execute(json.loads(raw))
    except BaseException:
        answer = {"status": "runtime_error"}
    sys.stdout.write(json.dumps(answer, allow_nan=False))
    sys.stdout.flush()
