from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSource:
    """A single RSS news source."""

    name: str
    url: str
    category: str


@dataclass(frozen=True)
class NewsAggregatorRequest:
    """Input for the news aggregator service."""

    sources: list[NewsSource]
    max_per_source: int = 5
