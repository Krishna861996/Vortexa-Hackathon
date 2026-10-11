from functools import lru_cache
from typing import Any

from supabase import Client, create_client
from fastapi import Depends

from .config import get_settings
from .auth import Identity, optional_identity


@lru_cache
def get_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_secret_key)


class Repository:
    def __init__(self, client: Client):
        self.client = client

    def list_challenges(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("challenges")
            .select("id,title,difficulty,concept_tags")
            .order("sort_order")
            .execute()
        )
        return response.data

    def get_challenge(self, challenge_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("challenges")
            .select("id,title,description,difficulty,function_name,starter_code,visible_tests,concept_tags")
            .eq("id", challenge_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        from .local_repository import CHALLENGES
        challenge = response.data[0]
        seed = next((item for item in CHALLENGES if item["id"] == challenge_id), None)
        challenge["hints"] = seed["hints"] if seed else []
        return challenge

    def get_hidden_tests(self, challenge_id: str) -> list[dict[str, Any]]:
        # Never grant user tokens access to hidden tests. Keep the runner's
        # private fixtures in the same server-only seed source used for SQL.
        from .local_repository import HIDDEN_TESTS
        return HIDDEN_TESTS.get(challenge_id, []).copy()

    def ensure_learner(self, learner_id: str) -> None:
        self.client.table("learners").upsert({"id": learner_id}, on_conflict="id", ignore_duplicates=True).execute()

    def get_learner(self, learner_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("learners")
            .select("id,hint_positions")
            .eq("id", learner_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def update_hint_positions(self, learner_id: str, positions: dict[str, int]) -> None:
        self.client.table("learners").update({"hint_positions": positions}).eq("id", learner_id).execute()

    def save_attempt(self, attempt: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("attempts").insert(attempt).execute()
        return response.data[0]

    def list_attempts(self, learner_id: str) -> list[dict[str, Any]]:
        attempts: list[dict[str, Any]] = []
        page_size = 1000
        while True:
            response = (
                self.client.table("attempts")
                .select("challenge_id,passed,concepts_practiced,test_results,submitted_code,submitted_at")
                .eq("learner_id", learner_id)
                .order("submitted_at", desc=True)
                .range(len(attempts), len(attempts) + page_size - 1)
                .execute()
            )
            attempts.extend(response.data)
            if len(response.data) < page_size:
                return attempts


def get_repository(identity: Identity | None = Depends(optional_identity)) -> Repository:
    if get_settings().codequest_storage == "local":
        from .local_repository import LocalRepository

        return LocalRepository()
    settings = get_settings()
    # A fresh request-scoped client prevents sessions leaking between users.
    client = create_client(settings.supabase_url, settings.supabase_publishable_key)
    if identity:
        client.postgrest.auth(identity.token)
    return Repository(client)
