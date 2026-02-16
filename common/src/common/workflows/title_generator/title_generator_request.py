"""Title-generator input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleGenRequest:
    """Defines what title-generator accepts."""

    tenant: str  # required — tenant identifier
    channel: str  # required — pinterest, youtube, instagram, etc.
    niche: str  # required
    keywords: tuple[str, ...]  # required — one or more keywords
    count: int = 1
