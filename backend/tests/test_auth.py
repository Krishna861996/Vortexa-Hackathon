import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID
import httpx
from fastapi.testclient import TestClient
from app.auth import Identity, optional_identity
from app.main import app
from app.repository import get_repository
from tests.test_api import FakeRepository

A = "00000000-0000-4000-8000-000000000001"
B = "00000000-0000-4000-8000-000000000002"


class AccountRepository(FakeRepository):
    def __init__(self):
        super().__init__()
        self.learners = {}
    def ensure_learner(self, id):
        self.learners.setdefault(id, {"id": id, "hint_positions": {}})
    def get_learner(self, id):
        return self.learners.get(id)
    def update_hint_positions(self, id, positions):
        self.learners[id]["hint_positions"] = positions
    def list_attempts(self, id):
        return [{**row, "submitted_at": "2026-10-11T00:00:00+00:00"} for row in self.attempts if row["learner_id"] == id]


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.repo = AccountRepository()
        app.dependency_overrides[get_repository] = lambda: self.repo
        self.client = TestClient(app)
    def tearDown(self):
        app.dependency_overrides.clear()

    def test_guest_can_browse_but_cannot_access_learning_records(self):
        self.assertEqual(self.client.get("/api/challenges").status_code, 200)
        for path, body in [("practice-attempts", {"code": "pass", "categories": ["passed"]}), ("hints/next", {}), ("mentor", {"question": "Help"}), ("attempts", {"code": "pass"})]:
            self.assertEqual(self.client.post(f"/api/challenges/add-numbers/{path}", json=body).status_code, 401)
        self.assertEqual(self.client.get("/api/me/progress").status_code, 401)

    def test_identity_comes_from_verified_token_and_accounts_are_isolated(self):
        app.dependency_overrides[optional_identity] = lambda: Identity(A, "token-a")
        response = self.client.post("/api/challenges/add-numbers/practice-attempts", json={"learner_id": B, "code": "return 5", "categories": ["passed"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.repo.attempts[0]["learner_id"], A)
        self.assertEqual(self.client.get(f"/api/learners/{B}/progress").status_code, 403)
        self.assertEqual(self.client.get("/api/me/progress").json()["total_attempts"], 1)
        self.client.post("/api/challenges/add-numbers/hints/next", json={})
        app.dependency_overrides[optional_identity] = lambda: Identity(B, "token-b")
        self.assertEqual(self.client.get("/api/me/progress").json()["total_attempts"], 0)
        self.assertEqual(self.repo.learners[B]["hint_positions"], {})

    def test_invalid_and_expired_tokens_fail_closed(self):
        settings = SimpleNamespace(supabase_url="https://example.supabase.co", supabase_publishable_key="public", supabase_secret_key="")
        with patch("app.auth.get_settings", return_value=settings), patch("app.auth.httpx.get", return_value=httpx.Response(401)):
            self.assertEqual(self.client.get("/api/me/progress", headers={"Authorization": "Bearer invalid"}).status_code, 401)
        with patch("app.auth.get_settings", return_value=settings), patch("app.auth.httpx.get", side_effect=httpx.ConnectError("offline")):
            self.assertEqual(self.client.get("/api/me/progress", headers={"Authorization": "Bearer expired"}).status_code, 503)

    def test_verified_user_endpoint_drives_identity(self):
        settings = SimpleNamespace(supabase_url="https://example.supabase.co", supabase_publishable_key="public", supabase_secret_key="")
        with patch("app.auth.get_settings", return_value=settings), patch("app.auth.httpx.get", return_value=httpx.Response(200, json={"id": A})) as request:
            response = self.client.get("/api/me/progress", headers={"Authorization": "Bearer supplied-token"})
            self.assertEqual(response.json()["learner_id"], A)
            self.assertEqual(request.call_args.kwargs["headers"]["Authorization"], "Bearer supplied-token")
