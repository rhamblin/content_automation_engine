"""News aggregator workflow — fetch and normalize RSS feeds."""

from common.workflows.linkedin.news_aggregator.news_aggregator_request import (
    NewsAggregatorRequest,
    NewsSource,
)
from common.workflows.linkedin.news_aggregator.news_aggregator_response import (
    NewsAggregatorResult,
    NewsArticle,
)
from common.workflows.linkedin.news_aggregator.news_aggregator_service import (
    NewsAggregatorService,
)

__all__ = [
    "NewsAggregatorRequest",
    "NewsAggregatorResult",
    "NewsAggregatorService",
    "NewsArticle",
    "NewsSource",
]
