from dataclasses import dataclass, field


@dataclass(frozen=True)
class NewsArticle:
    """A normalized article from an RSS feed."""

    title: str
    url: str
    summary: str
    published_date: str
    source_name: str
    category: str


@dataclass(frozen=True)
class NewsAggregatorResult:
    """Output from the news aggregator service."""

    articles: list[NewsArticle] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
