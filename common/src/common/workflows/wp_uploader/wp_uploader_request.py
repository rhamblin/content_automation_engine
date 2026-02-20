"""WP-uploader input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WpUploaderRequest:
    """Defines what wp-uploader accepts."""

    keywords: tuple[str, ...]  # required — list of keyword strings
    niche: str  # required — set by config loader
    status: str = "draft"  # draft | publish
