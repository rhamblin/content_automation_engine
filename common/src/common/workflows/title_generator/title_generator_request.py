"""Title-generator input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleGenRequest:
    """Defines what title-generator accepts."""

    channel: str  # required — pinterest, youtube, instagram, etc.
    niche: str  # required
    keyword: str  # required
    count: int = 3
    style: str = "mixed"  # mixed | clickbait | professional | casual | seo
