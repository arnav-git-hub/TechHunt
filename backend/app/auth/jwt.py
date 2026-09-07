"""JWT creation and verification.

Uses python-jose. Access tokens are short-lived (default 60 min).
Token payload: { "sub": "<user_id_str>", "exp": <epoch> }
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token.

    Args:
        subject: Typically the user UUID as a string.
        expires_delta: Override the default expiry window.

    Returns:
        Signed JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """Decode and validate a JWT access token.

    Returns:
        The subject (user ID string) if the token is valid, else None.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: Optional[str] = payload.get("sub")
        return sub
    except JWTError:
        return None
