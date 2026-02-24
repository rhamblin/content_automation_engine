"""WP-uploader input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KeywordEntry:
    """A keyword with optional intent and monetization metadata."""

    term: str
    intent: str = "informational"
    amazon_monetization_angle: str = ""


@dataclass(frozen=True)
class WpUploaderRequest:
    """Defines what wp-uploader accepts."""

    keywords: tuple[KeywordEntry, ...]  # required — list of keyword entries
    niche: str  # required — set by config loader
    status: str = "draft"  # draft | publish
