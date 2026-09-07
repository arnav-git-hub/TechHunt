"""Cross-dialect JSON type.

Uses PostgreSQL JSONB when running on PostgreSQL (production).
Falls back to SQLAlchemy's generic JSON type for SQLite (testing).

This allows the models to be tested with SQLite in-memory databases
while using the full JSONB capabilities in production.
"""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeEngine


class PortableJSON(JSON):
    """A JSON type that renders as JSONB on PostgreSQL and JSON on other dialects."""

    def load_dialect_impl(self, dialect) -> TypeEngine:  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
