"""Validate curated fixtures with trusted reference functions, never submissions."""
from collections import Counter
from itertools import groupby
from math import gcd
import unittest
from app.local_repository import CHALLENGES, HIDDEN_TESTS
from app.models import TestCase


def balanced(text):
    depth = 0
    for char in text:
        depth += 1 if char == "(" else -1
        if depth < 0:
            return False
    return depth == 0


REFERENCES = {
    "add-numbers": lambda a, b: a + b,
    "is-even": lambda n: n % 2 == 0,
    "sum-list": sum,
    "reverse-text": lambda text: text[::-1],
    "count-vowels": lambda text: sum(char.lower() in "aeiou" for char in text),
    "fizz-buzz": lambda n: ("Fizz" * (n % 3 == 0) + "Buzz" * (n % 5 == 0)) or str(n),
    "say-hello": lambda name: f"Hello, {name}!",
    "double-number": lambda n: n * 2,
    "rectangle-area": lambda w, h: w * h,
    "last-character": lambda text: text[-1:] if text else "",
    "larger-number": max,
    "absolute-value": abs,
    "count-positive": lambda numbers: sum(n > 0 for n in numbers),
    "palindrome": lambda text: text.lower() == text.lower()[::-1],
    "word-count": lambda text: len(text.split()),
    "largest-item": lambda numbers: max(numbers, default=0),
    "make-initials": lambda text: "".join(word[0].upper() for word in text.split()),
    "second-largest": lambda numbers: sorted(set(numbers))[-2] if len(set(numbers)) > 1 else 0,
    "longest-word": lambda text: max(text.split(), key=len, default=""),
    "compress-runs": lambda text: "".join(char for char, _ in groupby(text)),
    "balanced-parentheses": balanced,
    "is-prime": lambda n: n > 1 and all(n % i for i in range(2, n)),
    "unique-window": lambda text: max([0] + [j-i for i in range(len(text)) for j in range(i+1, len(text)+1) if len(set(text[i:j])) == j-i]),
    "binary-search": lambda numbers, target: numbers.index(target) if target in numbers else -1,
    "greatest-common-divisor": gcd,
}


class CatalogTests(unittest.TestCase):
    def test_five_questions_per_level_with_hints_and_private_cases(self):
        self.assertEqual(Counter(item["difficulty"] for item in CHALLENGES), dict.fromkeys(["beginner", "easy", "medium", "hard", "advanced"], 5))
        self.assertEqual(len({item["id"] for item in CHALLENGES}), 25)
        for item in CHALLENGES:
            self.assertEqual(len(item["hints"]), 3)
            self.assertGreaterEqual(len(item["visible_tests"]), 2)
            self.assertGreaterEqual(len(HIDDEN_TESTS[item["id"]]), 2)
            for case in item["visible_tests"] + HIDDEN_TESTS[item["id"]]:
                with self.subTest(challenge=item["id"], case=case):
                    parsed = TestCase.model_validate(case)
                    actual = REFERENCES[item["id"]](*parsed.input)
                    self.assertIs(type(actual), type(parsed.expected))
                    self.assertEqual(actual, parsed.expected)
