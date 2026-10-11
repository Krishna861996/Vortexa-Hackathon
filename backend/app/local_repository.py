"""Persistent local demo data for running the UI without Supabase credentials.

The real Supabase repository remains the default. Hidden tests stay in this
server-only module and are never returned by challenge detail endpoints.
"""

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "add-numbers", "title": "Add two numbers", "difficulty": "beginner",
        "description": "Return the sum of two integers a and b. Keep the function name and parameters as shown.",
        "function_name": "add_numbers", "starter_code": "def add_numbers(a, b):\n    # Return a + b\n    pass",
        "visible_tests": [{"input": [2, 3], "expected": 5}, {"input": [-1, 4], "expected": 3}],
        "hints": [
            "The function needs to give back one value made from both inputs.",
            "Which Python operator combines two numbers into their sum?",
            "Use that operator with both parameters, then return the result. Check a case with a negative number.",
        ],
        "concept_tags": ["functions", "arithmetic"],
    },
    {
        "id": "is-even", "title": "Check if a number is even", "difficulty": "easy",
        "description": "Return True when integer n is even, otherwise return False.",
        "function_name": "is_even", "starter_code": "def is_even(n):\n    # Return a boolean\n    pass",
        "visible_tests": [{"input": [4], "expected": True}, {"input": [7], "expected": False}],
        "hints": [
            "Look for a property that separates even numbers from odd numbers.",
            "The remainder after division by 2 can reveal that property.",
            "Compare that remainder with zero and return a boolean. Check both zero and a negative number.",
        ],
        "concept_tags": ["modulo", "booleans"],
    },
    {
        "id": "reverse-text", "title": "Reverse a string", "difficulty": "medium",
        "description": "Return text with its characters in reverse order. String slicing is available.",
        "function_name": "reverse_text", "starter_code": "def reverse_text(text):\n    # Return the reversed text\n    pass",
        "visible_tests": [{"input": ["code"], "expected": "edoc"}, {"input": ["a"], "expected": "a"}],
        "hints": [
            "Think about reading the characters from the end toward the start.",
            "A Python slice can move backward when its step is negative.",
            "Try a slice that covers the whole string with a backward step. Check one-character and empty text too.",
        ],
        "concept_tags": ["strings", "slicing"],
    },
    {
        "id": "count-vowels", "title": "Count vowels", "difficulty": "hard",
        "description": "Count a, e, i, o, and u in text, regardless of letter case. Use a for loop and basic string operations.",
        "function_name": "count_vowels", "starter_code": "def count_vowels(text):\n    count = 0\n    # Count vowels and return count\n    pass",
        "visible_tests": [{"input": ["hello"], "expected": 2}, {"input": ["SKY"], "expected": 0}],
        "hints": [
            "Keep a count as you inspect the text one character at a time.",
            "Normalize letter case before checking whether a character is a vowel.",
            "Increase the count only for vowel characters, and return it after the loop has visited the whole text.",
        ],
        "concept_tags": ["loops", "strings", "conditionals"],
    },
    {
        "id": "fizz-buzz", "title": "FizzBuzz value", "difficulty": "advanced",
        "description": "For integer n, return FizzBuzz if divisible by both 3 and 5, Fizz if only 3, Buzz if only 5, otherwise return n as a string.",
        "function_name": "fizz_buzz", "starter_code": "def fizz_buzz(n):\n    # Return a string for n\n    pass",
        "visible_tests": [{"input": [3], "expected": "Fizz"}, {"input": [5], "expected": "Buzz"}, {"input": [2], "expected": "2"}],
        "hints": [
            "Each word depends on whether the number is divisible by 3 or 5.",
            "Use the remainder operator to check divisibility, and remember a number can match both rules.",
            "Check the combined case before the individual cases. For a number matching neither, return its text form.",
        ],
        "concept_tags": ["conditionals", "modulo", "strings"],
    },
    {
        "id": "sum-list", "title": "Sum a list", "difficulty": "easy",
        "description": "Return the sum of the integers in numbers. Use a loop. An empty list should return 0.",
        "function_name": "sum_list", "starter_code": "def sum_list(numbers):\n    total = 0\n    # Visit each number and return the total\n    pass",
        "visible_tests": [{"input": [[1, 2, 3]], "expected": 6}, {"input": [[]], "expected": 0}],
        "hints": [
            "Think about building one running total from the values in the list.",
            "A for loop can visit each number, including when the list has no items.",
            "Update the running total for each item and return it after the loop. Check what stays in the total for an empty list.",
        ],
        "concept_tags": ["lists", "loops", "arithmetic"],
    },
]

HIDDEN_TESTS: dict[str, list[dict[str, Any]]] = {
    "add-numbers": [{"input": [0, 0], "expected": 0}, {"input": [-8, -5], "expected": -13}],
    "is-even": [{"input": [0], "expected": True}, {"input": [-3], "expected": False}],
    "reverse-text": [{"input": [""], "expected": ""}, {"input": ["Python"], "expected": "nohtyP"}],
    "count-vowels": [{"input": ["AEIOU"], "expected": 5}, {"input": ["CodeQuest"], "expected": 4}],
    "fizz-buzz": [{"input": [15], "expected": "FizzBuzz"}, {"input": [30], "expected": "FizzBuzz"}, {"input": [11], "expected": "11"}],
    "sum-list": [{"input": [[-2, 5, -1]], "expected": 2}, {"input": [[0]], "expected": 0}],
}


from .extra_challenges import EXTRA_CHALLENGES, EXTRA_HIDDEN_TESTS

CHALLENGES.extend(EXTRA_CHALLENGES)
HIDDEN_TESTS.update(EXTRA_HIDDEN_TESTS)
_levels = ["beginner", "easy", "medium", "hard", "advanced"]
CHALLENGES.sort(key=lambda item: _levels.index(item["difficulty"]))


class LocalRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(__file__).resolve().parent.parent / "demo.sqlite3"
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TABLE IF NOT EXISTS learners (id TEXT PRIMARY KEY, hint_positions TEXT NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id TEXT NOT NULL, learner_id TEXT NOT NULL,
                submitted_code TEXT NOT NULL, test_results TEXT NOT NULL,
                passed INTEGER NOT NULL, concepts_practiced TEXT NOT NULL,
                submitted_at TEXT NOT NULL
            )""")
            db.execute("INSERT OR IGNORE INTO learners (id, hint_positions) VALUES (?, ?)", ("demo-learner", "{}"))
            db.commit()

    def list_challenges(self) -> list[dict[str, Any]]:
        return [{key: challenge[key] for key in ("id", "title", "difficulty", "concept_tags")} for challenge in CHALLENGES]

    def get_challenge(self, challenge_id: str) -> dict[str, Any] | None:
        return next((challenge.copy() for challenge in CHALLENGES if challenge["id"] == challenge_id), None)

    def get_hidden_tests(self, challenge_id: str) -> list[dict[str, Any]]:
        return HIDDEN_TESTS.get(challenge_id, []).copy()

    def get_learner(self, learner_id: str) -> dict[str, Any] | None:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute("SELECT id, hint_positions FROM learners WHERE id = ?", (learner_id,)).fetchone()
        return {"id": row[0], "hint_positions": json.loads(row[1])} if row else None

    def update_hint_positions(self, learner_id: str, positions: dict[str, int]) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE learners SET hint_positions = ? WHERE id = ?", (json.dumps(positions), learner_id))
            db.commit()

    def ensure_learner(self, learner_id: str) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT OR IGNORE INTO learners (id, hint_positions) VALUES (?, '{}')", (learner_id,))
            db.commit()

    def save_attempt(self, attempt: dict[str, Any]) -> dict[str, Any]:
        submitted_at = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(self.path)) as db:
            cursor = db.execute(
                """INSERT INTO attempts (challenge_id, learner_id, submitted_code, test_results,
                   passed, concepts_practiced, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (attempt["challenge_id"], attempt["learner_id"], attempt["submitted_code"],
                 json.dumps(attempt["test_results"]), int(attempt["passed"]),
                 json.dumps(attempt["concepts_practiced"]), submitted_at),
            )
            db.commit()
            return {"id": cursor.lastrowid, "submitted_at": submitted_at}

    def list_attempts(self, learner_id: str) -> list[dict[str, Any]]:
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(
                """SELECT challenge_id, passed, concepts_practiced, test_results,
                   submitted_code, submitted_at
                   FROM attempts WHERE learner_id = ? ORDER BY submitted_at DESC, id DESC""",
                (learner_id,),
            ).fetchall()
        return [
            {"challenge_id": row[0], "passed": bool(row[1]),
             "concepts_practiced": json.loads(row[2]),
             "test_results": json.loads(row[3]), "submitted_code": row[4],
             "submitted_at": row[5]}
            for row in rows
        ]
