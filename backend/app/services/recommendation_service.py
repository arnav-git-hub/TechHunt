"""Transparent, deterministic personalized opportunity suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.user import User


@dataclass(frozen=True)
class SuggestedEvent:
    """One scored event and its plain-language matching explanation."""

    event: Event
    score: float
    explanation: str


class RecommendationService:
    """Generate explainable suggestions from user interests and skills only."""

    def __init__(self, db: AsyncSession) -> None:
        """Create the service with an async database session."""
        self._db = db

    async def suggest_for_user(self, user: User, limit: int = 20) -> list[SuggestedEvent]:
        """Return event suggestions based on direct, visible profile-term matches."""
        profile_terms = {item.interest.casefold() for item in user.interests}
        profile_terms.update(item.skill.casefold() for item in user.skills)
        if not profile_terms:
            return []

        result = await self._db.execute(
            select(Event)
            .options(
                selectinload(Event.tags),
                selectinload(Event.skills),
                selectinload(Event.technologies),
            )
            .where(Event.event_status == "published")
        )
        suggestions: list[SuggestedEvent] = []
        for event in result.scalars():
            event_terms = {tag.tag.casefold() for tag in event.tags}
            event_terms.update(skill.skill.casefold() for skill in event.skills)
            event_terms.update(technology.technology.casefold() for technology in event.technologies)
            if event.category:
                event_terms.add(event.category.casefold())
            if event.opportunity_type:
                event_terms.add(event.opportunity_type.casefold())
            matches = sorted(profile_terms.intersection(event_terms))
            if matches:
                suggestions.append(
                    SuggestedEvent(
                        event=event,
                        score=round(len(matches) / len(profile_terms), 4),
                        explanation=f"Matches your profile: {', '.join(matches[:3])}.",
                    )
                )
        return sorted(suggestions, key=lambda item: item.score, reverse=True)[:limit]
