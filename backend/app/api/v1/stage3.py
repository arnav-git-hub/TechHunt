"""Phase 3 routes for search, submissions, saved events, and source ingestion."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.events import _event_to_summary
from app.auth.admin import get_current_admin
from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models.admin import EventSource, OrganizerSubmission
from app.models.auth import Notification
from app.models.event import Event, SavedEvent
from app.models.user import User, UserInterest, UserSkill
from app.schemas.event import PaginatedEvents
from app.schemas.stage3 import (
    EventSearchRequest,
    EventSourceResponse,
    IngestionRunResponse,
    AdminSubmissionResponse,
    NotificationResponse,
    OrganizerSubmissionRequest,
    OrganizerSubmissionResponse,
    SavedEventResponse,
    SubmissionReviewRequest,
)
from app.schemas.stage4 import (
    NaturalLanguageSearchRequest,
    NaturalLanguageSearchResponse,
    RecommendationResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.services.event_service import EventService, compute_pages
from app.services.ingestion_service import IngestionService
from app.services.natural_search_service import interpret_natural_query
from app.services.recommendation_service import RecommendationService
from app.utils.slug import make_unique_slug

router = APIRouter(tags=["phase-3", "phase-4"])


def _parse_submission_datetime(value: object) -> datetime | None:
    """Convert a JSON-serialized submission timestamp back to a UTC datetime."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Submission timestamps must be ISO 8601 strings.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


@router.post("/events/search", response_model=PaginatedEvents)
async def search_events(
    filters: EventSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> PaginatedEvents:
    """Search published events with a JSON body for structured clients."""
    items, total = await EventService(db).list_events(filters)
    return PaginatedEvents(
        items=[_event_to_summary(event) for event in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=compute_pages(total, filters.page_size),
    )


@router.post("/events/natural-search", response_model=NaturalLanguageSearchResponse)
async def natural_search_events(
    request: NaturalLanguageSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> NaturalLanguageSearchResponse:
    """Search with conservative plain-language interpretation; no AI provider is called."""
    filters, interpreted = interpret_natural_query(request.query, request.page, request.page_size)
    items, total = await EventService(db).list_events(filters)
    return NaturalLanguageSearchResponse(
        items=[_event_to_summary(event) for event in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=compute_pages(total, filters.page_size),
        interpreted_filters=interpreted,
    )


@router.post("/submissions", response_model=OrganizerSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: OrganizerSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizerSubmissionResponse:
    """Store an organizer submission for later administrator moderation."""
    submission = OrganizerSubmission(user_id=current_user.id, raw_payload=payload.model_dump(mode="json"))
    db.add(submission)
    await db.flush()
    return OrganizerSubmissionResponse.model_validate(submission)


@router.get("/users/me/notifications", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    """List the authenticated user's newest in-app notifications first."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return [NotificationResponse.model_validate(notification) for notification in result.scalars()]


@router.put("/users/me/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    payload: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesResponse:
    """Update the profile interests and skills used for personalized suggestions."""
    user = await db.scalar(
        select(User)
        .options(selectinload(User.interests), selectinload(User.skills))
        .where(User.id == current_user.id)
    )
    assert user is not None
    user.bio = payload.bio
    user.location = payload.location
    user.experience_level = payload.experience_level
    user.interests = [
        UserInterest(interest=value.strip()) for value in sorted(set(payload.interests)) if value.strip()
    ]
    user.skills = [
        UserSkill(skill=value.strip()) for value in sorted(set(payload.skills)) if value.strip()
    ]
    await db.flush()
    return UserPreferencesResponse(
        bio=user.bio,
        location=user.location,
        experience_level=user.experience_level,
        interests=[item.interest for item in user.interests],
        skills=[item.skill for item in user.skills],
    )


@router.get("/users/me/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationResponse]:
    """Return transparent personalized suggestions based only on saved profile terms."""
    user = await db.scalar(
        select(User)
        .options(selectinload(User.interests), selectinload(User.skills))
        .where(User.id == current_user.id)
    )
    assert user is not None
    suggestions = await RecommendationService(db).suggest_for_user(user)
    return [
        RecommendationResponse(
            event=_event_to_summary(item.event), score=item.score, explanation=item.explanation
        )
        for item in suggestions
    ]


@router.post("/users/me/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Mark one of the current user's notifications as read."""
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)


@router.get("/users/me/saved-events", response_model=list[SavedEventResponse])
async def list_saved_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedEventResponse]:
    """List the authenticated user's saved published events."""
    result = await db.execute(
        select(SavedEvent)
        .options(
            selectinload(SavedEvent.event).selectinload(Event.tags),
            selectinload(SavedEvent.event).selectinload(Event.technologies),
        )
        .where(SavedEvent.user_id == current_user.id, Event.event_status == "published")
        .join(Event)
        .order_by(SavedEvent.saved_at.desc())
    )
    return [SavedEventResponse(event=_event_to_summary(row.event), saved_at=row.saved_at) for row in result.scalars()]


@router.post("/events/{event_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def save_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Save one published event for the authenticated user."""
    event = await db.get(Event, event_id)
    if event is None or event.event_status != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    existing = await db.get(SavedEvent, {"user_id": current_user.id, "event_id": event_id})
    if existing is None:
        db.add(SavedEvent(user_id=current_user.id, event_id=event_id))


@router.delete("/events/{event_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a saved event; deleting a missing bookmark is idempotent."""
    saved = await db.get(SavedEvent, {"user_id": current_user.id, "event_id": event_id})
    if saved is not None:
        await db.delete(saved)


@router.get("/admin/sources", response_model=list[EventSourceResponse])
async def list_sources(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[EventSourceResponse]:
    """List the registered connector sources and their operational state."""
    return [EventSourceResponse.model_validate(source) for source in await IngestionService(db).list_sources()]


@router.get("/admin/submissions", response_model=list[AdminSubmissionResponse])
async def list_submissions(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSubmissionResponse]:
    """Return the organizer-submission moderation queue."""
    result = await db.execute(
        select(OrganizerSubmission).order_by(OrganizerSubmission.created_at.desc())
    )
    return [AdminSubmissionResponse.model_validate(submission) for submission in result.scalars()]


@router.post("/admin/submissions/{submission_id}/review", response_model=AdminSubmissionResponse)
async def review_submission(
    submission_id: uuid.UUID,
    payload: SubmissionReviewRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSubmissionResponse:
    """Approve or reject a pending organizer submission and notify its author."""
    submission = await db.get(OrganizerSubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")
    if submission.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Submission has already been reviewed.")

    submission.status = payload.decision
    submission.reviewed_by = current_user.id
    notification_payload: dict[str, str] = {"submission_id": str(submission.id)}
    if payload.decision == "approved":
        details = submission.raw_payload or {}
        event = Event(
            title=str(details["title"]),
            slug=make_unique_slug(str(details["title"])),
            description=str(details["description"]),
            source="organizer_submission",
            source_event_id=str(submission.id),
            event_url=str(details["event_url"]),
            organizer=details.get("organizer"),
            opportunity_type=str(details["opportunity_type"]),
            start_at_utc=_parse_submission_datetime(details.get("start_at_utc")),
            registration_deadline_utc=_parse_submission_datetime(
                details.get("registration_deadline_utc")
            ),
            is_online=bool(details.get("is_online")),
            location=details.get("location"),
            price_type="unknown",
            event_status="published",
            published_at=datetime.now(timezone.utc),
        )
        db.add(event)
        notification_payload["event_title"] = event.title
    db.add(
        Notification(
            user_id=submission.user_id,
            type=f"submission_{payload.decision}",
            payload=notification_payload,
        )
    )
    await db.flush()
    return AdminSubmissionResponse.model_validate(submission)


@router.post("/admin/ingest/{source_key}", response_model=IngestionRunResponse)
async def ingest_source(
    source_key: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> IngestionRunResponse:
    """Run an enabled source ingestion job; only the mock source is enabled now."""
    try:
        run = await IngestionService(db).ingest(source_key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    source = await db.get(EventSource, run.source_id)
    assert source is not None
    return IngestionRunResponse(
        id=run.id,
        source_key=source.connector_key,
        events_fetched=run.events_fetched,
        events_created=run.events_created,
        events_updated=run.events_updated,
        errors=run.errors,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )
