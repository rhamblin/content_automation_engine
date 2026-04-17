import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.app_logger import AppLogger
from common.workflows.linkedin.news_aggregator.news_aggregator_request import (
    NewsAggregatorRequest,
    NewsSource,
)
from common.workflows.linkedin.news_aggregator.news_aggregator_response import (
    NewsAggregatorResult,
    NewsArticle,
)


class NewsAggregatorService:
    """Fetch and normalize articles from RSS feeds.

    Stateless service — no file I/O. Suitable for use in both
    dev-tools and Docker services.
    """

    def __init__(self) -> None:
        self.logger = AppLogger(__name__)

    def aggregate(self, request: NewsAggregatorRequest) -> NewsAggregatorResult:
        """Fetch articles from all sources, return normalized results."""
        all_articles: list[NewsArticle] = []
        errors: list[str] = []

        for source in request.sources:
            try:
                articles = self._fetch_source(source, request.max_per_source)
                all_articles.extend(articles)
                self.logger.info(
                    f"Fetched {len(articles)} articles from {source.name}"
                )
            except Exception as e:
                msg = f"Failed to fetch {source.name}: {e}"
                self.logger.error(msg)
                errors.append(msg)

        all_articles.sort(key=lambda a: a.published_date, reverse=True)
        return NewsAggregatorResult(articles=all_articles, errors=errors)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ConnectionError),
        reraise=True,
    )
    def _fetch_source(
        self, source: NewsSource, max_articles: int
    ) -> list[NewsArticle]:
        """Fetch and parse a single RSS feed."""
        feed = feedparser.parse(source.url)

        if feed.bozo and not feed.entries:
            raise ConnectionError(
                f"Feed parse error for {source.url}: {feed.bozo_exception}"
            )

        articles: list[NewsArticle] = []
        for entry in feed.entries[:max_articles]:
            article = self._normalize_entry(entry, source)
            if article:
                articles.append(article)

        return articles

    def _normalize_entry(
        self, entry: dict, source: NewsSource
    ) -> NewsArticle | None:
        """Convert a feedparser entry to a NewsArticle."""
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        if not title or not link:
            return None

        summary_raw = entry.get("summary", "") or entry.get("description", "")
        summary = self._clean_html(summary_raw)[:500]

        published_date = self._parse_date(entry)

        return NewsArticle(
            title=title,
            url=link,
            summary=summary,
            published_date=published_date,
            source_name=source.name,
            category=source.category,
        )

    @staticmethod
    def _parse_date(entry: dict) -> str:
        """Extract and normalize publish date to ISO 8601."""
        for field in ("published", "updated", "created"):
            raw = entry.get(field)
            if raw:
                try:
                    dt = parsedate_to_datetime(raw)
                    return dt.astimezone(timezone.utc).isoformat()
                except (ValueError, TypeError):
                    pass

        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed:
            try:
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except (ValueError, TypeError):
                pass

        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _clean_html(text: str) -> str:
        """Strip HTML tags and decode entities."""
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
        return text.strip()
