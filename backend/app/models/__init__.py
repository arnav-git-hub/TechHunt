"""SQLAlchemy ORM models package.

Import all models here so Alembic can auto-detect schema changes.
"""

from app.models.user import User, UserInterest, UserSkill  # noqa: F401
from app.models.event import (  # noqa: F401
    Event,
    EventTag,
    EventSkill,
    EventTechnology,
    SavedEvent,
)
from app.models.auth import Notification, Recommendation  # noqa: F401
from app.models.admin import (  # noqa: F401
    OrganizerSubmission,
    EventSource,
    IngestionRun,
    AdminAuditLog,
)
