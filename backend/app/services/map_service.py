"""Provider-free map links for physical event locations."""

from urllib.parse import quote_plus

from app.models.event import Event


def build_map_url(event: Event) -> str | None:
    """Return an OpenStreetMap search URL without exposing a map API key."""
    if event.latitude is not None and event.longitude is not None:
        return f"https://www.openstreetmap.org/?mlat={event.latitude}&mlon={event.longitude}"
    location = event.location or ", ".join(part for part in (event.city, event.country) if part)
    return f"https://www.openstreetmap.org/search?query={quote_plus(location)}" if location else None
