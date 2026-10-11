from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from .config import get_settings


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
            .select("id,title,description,difficulty,function_name,starter_code,visible_tests,hints,concept_tags")
            .eq("id", challenge_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_hidden_tests(self, challenge_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("challenge_hidden_tests")
            .select("tests")
            .eq("challenge_id", challenge_id)
            .limit(1)
            .execute()
        )
        return response.data[0]["tests"] if response.data else []

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


def get_repository() -> Repository:
    if get_settings().codequest_storage == "local":
        from .local_repository import LocalRepository

        return LocalRepository()
    return Repository(get_client())
