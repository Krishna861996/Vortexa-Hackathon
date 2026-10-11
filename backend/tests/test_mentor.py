import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from app.mentor import ask_mentor

class MentorTests(unittest.TestCase):
    challenge = {"description": "Return the sum", "concept_tags": ["arithmetic"], "hidden_tests": [{"secret": "never-send"}]}

    def test_missing_key_uses_local(self):
        with patch("app.mentor.get_settings", return_value=SimpleNamespace(gemini_api_key="")):
            self.assertEqual(ask_mentor(self.challenge, "Help", "pass").source, "local")

    def test_gemini_response_and_private_context(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"candidates": [{"content": {"parts": [{"text": "Trace one example."}]}}]}).encode()
        settings = SimpleNamespace(gemini_api_key="test-secret", gemini_model="gemini-flash-latest")
        with patch("app.mentor.get_settings", return_value=settings), patch("app.mentor.urllib.request.urlopen", return_value=response) as call:
            result = ask_mentor(self.challenge, "Help", "pass")
            self.assertEqual(result.source, "gemini")
            self.assertEqual(result.answer, "Trace one example.")
            self.assertNotIn("never-send", call.call_args.args[0].data.decode())

    def test_network_failure_uses_local(self):
        settings = SimpleNamespace(gemini_api_key="test", gemini_model="gemini-flash-latest")
        with patch("app.mentor.get_settings", return_value=settings), patch("app.mentor.urllib.request.urlopen", side_effect=TimeoutError):
            self.assertEqual(ask_mentor(self.challenge, "Help", "pass").source, "local")
