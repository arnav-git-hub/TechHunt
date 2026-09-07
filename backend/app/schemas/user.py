"""User Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import AppBaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserRegisterRequest(AppBaseModel):
    """Body for POST /api/v1/auth/register."""

    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class UserLoginRequest(AppBaseModel):
    """Body for POST /api/v1/auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(AppBaseModel):
    """Public user profile returned by the API. Never includes password_hash."""

    id: uuid.UUID
    name: str
    email: str
    role: str
    bio: Optional[str] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TokenResponse(AppBaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginResponse(AppBaseModel):
    """Combined login response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
