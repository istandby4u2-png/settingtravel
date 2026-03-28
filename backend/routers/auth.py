from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from auth.google_auth import (
    get_auth_url,
    exchange_code,
    is_authenticated,
    logout,
)

router = APIRouter()

REDIRECT_PATH = "/api/auth/google/callback"


def _build_redirect_uri(request: Request) -> str:
    return f"http://localhost:8000{REDIRECT_PATH}"


@router.get("/google/status")
async def google_auth_status():
    return {"authenticated": is_authenticated()}


@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = _build_redirect_uri(request)
    url = get_auth_url(redirect_uri)
    if not url:
        return {"error": "GOOGLE_CLIENT_ID가 설정되지 않았습니다. .env 파일을 확인하세요."}
    return {"auth_url": url}


@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(url=f"http://localhost:3000/photos?error={error}")

    if not code:
        return RedirectResponse(url="http://localhost:3000/photos?error=no_code")

    redirect_uri = _build_redirect_uri(request)
    token = await exchange_code(code, redirect_uri)

    if not token:
        return RedirectResponse(url="http://localhost:3000/photos?error=token_exchange_failed")

    return RedirectResponse(url="http://localhost:3000/photos?auth=success")


@router.post("/google/logout")
async def google_logout():
    logout()
    return {"message": "로그아웃되었습니다."}
