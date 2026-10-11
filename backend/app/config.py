from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    codequest_storage: str = "supabase"
    supabase_url: str = ""
    supabase_secret_key: str = ""
    cors_origins: str = "http://localhost:3000"
    codequest_runner: str = "piston"
    piston_url: str = "https://emkc.org/api/v2/piston"
    piston_token: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_storage(self):
        if self.codequest_storage not in {"supabase", "local"}:
            raise ValueError("CODEQUEST_STORAGE must be 'supabase' or 'local'")
        if self.codequest_storage == "supabase" and not (self.supabase_url and self.supabase_secret_key):
            raise ValueError("Supabase mode requires SUPABASE_URL and SUPABASE_SECRET_KEY; set CODEQUEST_STORAGE=local for the local demo")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

