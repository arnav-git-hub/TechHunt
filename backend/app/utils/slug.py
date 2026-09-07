"""Slug generation utility.

Produces URL-safe, human-readable slugs from event titles.
Appends a short UUID fragment to guarantee uniqueness.
"""

import re
import uuid


def slugify(text: str) -> str:
    """Convert a string to a URL-safe slug.

    Examples:
        "Global AI Hackathon 2025" -> "global-ai-hackathon-2025"
    """
    text = text.lower().strip()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


def make_unique_slug(title: str) -> str:
    """Generate a unique slug by appending a short UUID fragment."""
    base = slugify(title)
    suffix = uuid.uuid4().hex[:8]
    return f"{base}-{suffix}"
