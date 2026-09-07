"""Conservative natural-language query interpretation without external AI calls."""

from __future__ import annotations

import re

from app.schemas.event import EventFilters

_TYPE_TERMS = {
    "hackathon": "hackathon",
    "workshop": "workshop",
    "meetup": "meetup",
    "conference": "conference",
    "fellowship": "fellowship",
    "scholarship": "scholarship",
    "grant": "grant",
}


def interpret_natural_query(query: str, page: int, page_size: int) -> tuple[EventFilters, list[str]]:
    """Interpret only unambiguous discovery words and preserve the rest as text search."""
    lowered = query.casefold()
    interpreted: list[str] = []
    filters = EventFilters(page=page, page_size=page_size)
    for term, opportunity_type in _TYPE_TERMS.items():
        if re.search(rf"\b{re.escape(term)}s?\b", lowered):
            filters.opportunity_type = opportunity_type
            interpreted.append(f"type: {opportunity_type}")
            break
    if re.search(r"\bonline\b", lowered):
        filters.is_online = True
        interpreted.append("format: online")
    elif re.search(r"\b(in[ -]?person|offline)\b", lowered):
        filters.is_online = False
        interpreted.append("format: in-person")
    if re.search(r"\bfree\b", lowered):
        filters.price_type = "free"
        interpreted.append("price: free")

    searchable = re.sub(
        r"\b(free|online|offline|in[ -]?person|"
        + "|".join(f"{term}s?" for term in _TYPE_TERMS)
        + r")\b",
        " ",
        query,
        flags=re.IGNORECASE,
    )
    searchable = re.sub(r"\s+", " ", searchable).strip(" ,.-")
    filters.q = searchable or None
    return filters, interpreted
