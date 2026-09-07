"""Password hashing and verification utilities.

Uses the `bcrypt` library directly. Never store plain-text passwords.

Note: passlib 1.7.x is incompatible with bcrypt 4.x (API change in bcrypt).
We call bcrypt directly to avoid this version mismatch.
"""

import bcrypt


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:  # noqa: BLE001
        return False
