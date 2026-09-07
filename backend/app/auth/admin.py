"""Authorization dependencies for administrator-only API routes."""

from fastapi import Depends, HTTPException, status

from app.auth.deps import get_current_user
from app.models.user import User


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Return the current user when they hold the administrator role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required.",
        )
    return current_user
