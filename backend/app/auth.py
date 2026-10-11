"""Validate bearer tokens with Supabase Auth; never trust a client learner ID."""
from dataclasses import dataclass
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Identity:
    id: str
    token: str


def optional_identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Identity | None:
    if credentials is None:
        return None
    settings = get_settings()
    key = settings.supabase_publishable_key or settings.supabase_secret_key
    if not settings.supabase_url or not key:
        raise HTTPException(503, "Supabase login is not configured on the API.")
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
            headers={"apikey": key, "Authorization": f"Bearer {credentials.credentials}"}, timeout=10,
        )
    except httpx.HTTPError:
        raise HTTPException(503, "Could not verify your login. Please retry shortly.") from None
    if response.status_code in (401, 403):
        raise HTTPException(401, "Your session has expired. Please log in again.")
    if response.status_code != 200:
        raise HTTPException(503, "Login verification is temporarily unavailable.")
    try:
        user_id = str(UUID(response.json()["id"]))
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "Invalid login session.") from None
    return Identity(user_id, credentials.credentials)


def current_identity(identity: Identity | None = Depends(optional_identity)) -> Identity:
    if identity is None:
        raise HTTPException(401, "Log in to save progress and practice challenges.")
    return identity
