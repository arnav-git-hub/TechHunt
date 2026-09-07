"""Auth service: user registration and login business logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserLoginRequest, UserRegisterRequest


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, data: UserRegisterRequest) -> tuple[User, str]:
        """Create a new user account and return (user, access_token).

        Raises:
            ValueError: If the email is already registered.
        """
        # Check for duplicate email
        existing = await self._db.execute(
            select(User).where(User.email == data.email.lower())
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Email address is already registered.")

        user = User(
            name=data.name.strip(),
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role="user",
        )
        self._db.add(user)
        await self._db.flush()  # populate user.id

        token = create_access_token(str(user.id))
        return user, token

    async def login(self, data: UserLoginRequest) -> tuple[User, str]:
        """Authenticate a user and return (user, access_token).

        Raises:
            ValueError: If credentials are invalid.
        """
        result = await self._db.execute(
            select(User).where(User.email == data.email.lower())
        )
        user = result.scalar_one_or_none()

        if user is None or user.password_hash is None:
            raise ValueError("Invalid email or password.")

        if not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid email or password.")

        token = create_access_token(str(user.id))
        return user, token
