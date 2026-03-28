"""Google OAuth 2.0 authentication for Photos Library API."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

import httpx

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
TOKEN_PATH = Path(__file__).parent.parent / "data" / "google_token.json"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def _get_client_config() -> tuple[str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    return client_id, client_secret


def get_auth_url(redirect_uri: str) -> str | None:
    client_id, _ = _get_client_config()
    if not client_id:
        return None

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    qs = "&".join(f"{k}={httpx.URL('', params={k: v}).params[k]}" for k, v in params.items())
    return f"{AUTH_URL}?{qs}"


async def exchange_code(code: str, redirect_uri: str) -> dict | None:
    client_id, client_secret = _get_client_config()
    if not client_id or not client_secret:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code != 200:
            print(f"[auth] Token exchange failed: {resp.text}", flush=True)
            return None

        token_data = resp.json()
        token_data["obtained_at"] = datetime.now(timezone.utc).isoformat()
        _save_token(token_data)
        return token_data


async def refresh_access_token() -> dict | None:
    token = _load_token()
    if not token or "refresh_token" not in token:
        return None

    client_id, client_secret = _get_client_config()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "refresh_token": token["refresh_token"],
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code != 200:
            print(f"[auth] Token refresh failed: {resp.text}", flush=True)
            return None

        new_data = resp.json()
        token["access_token"] = new_data["access_token"]
        if "refresh_token" in new_data:
            token["refresh_token"] = new_data["refresh_token"]
        token["expires_in"] = new_data.get("expires_in", 3600)
        token["obtained_at"] = datetime.now(timezone.utc).isoformat()
        _save_token(token)
        return token


async def get_valid_access_token() -> str | None:
    token = _load_token()
    if not token:
        return None

    obtained = datetime.fromisoformat(token.get("obtained_at", "2000-01-01T00:00:00+00:00"))
    expires_in = token.get("expires_in", 3600)
    now = datetime.now(timezone.utc)

    if (now - obtained).total_seconds() > (expires_in - 120):
        token = await refresh_access_token()
        if not token:
            return None

    return token.get("access_token")


def is_authenticated() -> bool:
    return _load_token() is not None


def logout():
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


def _save_token(token_data: dict):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2), encoding="utf-8")


def _load_token() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    try:
        return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
