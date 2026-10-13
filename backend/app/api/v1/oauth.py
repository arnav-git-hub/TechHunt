"""OAuth routes for Google and GitHub (Stage 6).

Both providers are implemented using Authlib's async OAuth 2.0 client.
When the corresponding client credentials are absent from settings, all
routes return HTTP 503 so the frontend can surface a clear "not available"
state rather than a cryptic error.

Google flow:  GET /auth/google  →  redirect  →  GET /auth/google/callback
GitHub flow:  GET /auth/github  →  redirect  →  GET /auth/github/callback

On success each callback issues a JWT and returns the same LoginResponse
shape as the email/password login endpoint so the frontend can reuse its
existing auth logic.
"""

from __future__ import annotations

import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import LoginResponse, UserResponse
from app.services.analytics_service import analytics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth", "oauth"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOOGLE_CONF = {
    "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "access_token_url": "https://oauth2.googleapis.com/token",
    "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
    "client_kwargs": {"scope": "openid email profile"},
}

_GITHUB_CONF = {
    "authorize_url": "https://github.com/login/oauth/authorize",
    "access_token_url": "https://github.com/login/oauth/access_token",
    "userinfo_url": "https://api.github.com/user",
    "client_kwargs": {"scope": "read:user user:email"},
}


def _require_google() -> None:
    """Raise 503 when Google OAuth credentials are not configured."""
    if not (settings.google_client_id and settings.google_client_secret):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server.",
        )


def _require_github() -> None:
    """Raise 503 when GitHub OAuth credentials are not configured."""
    if not (settings.github_client_id and settings.github_client_secret):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured on this server.",
        )


def _build_oauth_client(provider: str, client_id: str, client_secret: str, conf: dict):  # type: ignore[return]
    """Return a configured Authlib AsyncOAuth2Client."""
    try:
        from authlib.integrations.httpx_client import AsyncOAuth2Client  # type: ignore[import-untyped]

        return AsyncOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            **conf.get("client_kwargs", {}),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("OAuth: could not build %s client — %s", provider, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider} OAuth client unavailable.",
        ) from exc


async def _upsert_oauth_user(db: AsyncSession, *, email: str, name: str, provider: str) -> tuple[User, str]:
    """Find or create a user record for an OAuth login.

    OAuth users have a random password_hash so the account cannot be
    used with the email/password endpoint.
    """
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    is_new = user is None
    if user is None:
        user = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(secrets.token_hex(32)),
            role="user",
        )
        db.add(user)
        await db.flush()

    token = create_access_token(str(user.id))
    if is_new:
        analytics.capture(
            distinct_id=str(user.id),
            event="user_registered",
            properties={"provider": provider},
        )
    else:
        analytics.capture(
            distinct_id=str(user.id),
            event="user_login_oauth",
            properties={"provider": provider},
        )
    return user, token


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@router.get("/google", summary="Begin Google OAuth flow")
async def google_login(request: Request) -> RedirectResponse:
    """Redirect the user to Google's OAuth consent screen."""
    _require_google()
    client = _build_oauth_client(
        "Google",
        settings.google_client_id,
        settings.google_client_secret,
        _GOOGLE_CONF,
    )
    redirect_uri = str(request.url_for("google_callback"))
    uri, _state = client.create_authorization_url(
        _GOOGLE_CONF["authorize_url"],
        redirect_uri=redirect_uri,
    )
    return RedirectResponse(uri)


@router.get("/google/callback", response_model=LoginResponse, name="google_callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Handle Google OAuth callback, issue a JWT, and return LoginResponse."""
    _require_google()
    client = _build_oauth_client(
        "Google",
        settings.google_client_id,
        settings.google_client_secret,
        _GOOGLE_CONF,
    )
    redirect_uri = str(request.url_for("google_callback"))
    try:
        token = await client.fetch_token(
            _GOOGLE_CONF["access_token_url"],
            authorization_response=str(request.url),
            redirect_uri=redirect_uri,
        )
        resp = await client.get(_GOOGLE_CONF["userinfo_url"], token=token)
        resp.raise_for_status()
        info = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("Google OAuth callback error — %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to complete Google OAuth handshake.",
        ) from exc

    email: str | None = info.get("email")
    name: str = info.get("name") or info.get("email", "Google User")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return an email address.",
        )

    user, jwt_token = await _upsert_oauth_user(db, email=email, name=name, provider="google")
    return LoginResponse(
        access_token=jwt_token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------

@router.get("/github", summary="Begin GitHub OAuth flow")
async def github_login(request: Request) -> RedirectResponse:
    """Redirect the user to GitHub's OAuth consent screen."""
    _require_github()
    client = _build_oauth_client(
        "GitHub",
        settings.github_client_id,
        settings.github_client_secret,
        _GITHUB_CONF,
    )
    redirect_uri = str(request.url_for("github_callback"))
    uri, _state = client.create_authorization_url(
        _GITHUB_CONF["authorize_url"],
        redirect_uri=redirect_uri,
    )
    return RedirectResponse(uri)


@router.get("/github/callback", response_model=LoginResponse, name="github_callback")
async def github_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Handle GitHub OAuth callback, issue a JWT, and return LoginResponse."""
    _require_github()
    client = _build_oauth_client(
        "GitHub",
        settings.github_client_id,
        settings.github_client_secret,
        _GITHUB_CONF,
    )
    redirect_uri = str(request.url_for("github_callback"))
    try:
        token = await client.fetch_token(
            _GITHUB_CONF["access_token_url"],
            authorization_response=str(request.url),
            redirect_uri=redirect_uri,
        )
        resp = await client.get(_GITHUB_CONF["userinfo_url"], token=token)
        resp.raise_for_status()
        info = resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("GitHub OAuth callback error — %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to complete GitHub OAuth handshake.",
        ) from exc

    # GitHub may not return an email if the user has it set to private.
    # In that case we request the /user/emails endpoint.
    email: str | None = info.get("email")
    if not email:
        try:
            emails_resp = await client.get(
                "https://api.github.com/user/emails", token=token
            )
            emails_resp.raise_for_status()
            emails = emails_resp.json()
            primary = next(
                (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                None,
            )
            email = primary
        except Exception as exc:  # noqa: BLE001
            logger.warning("GitHub: could not fetch user emails — %s", exc)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub did not return a verified email address. "
                   "Please make your email public on GitHub or use email/password login.",
        )

    name: str = info.get("name") or info.get("login") or "GitHub User"
    user, jwt_token = await _upsert_oauth_user(db, email=email, name=name, provider="github")
    return LoginResponse(
        access_token=jwt_token,
        user=UserResponse.model_validate(user),
    )
