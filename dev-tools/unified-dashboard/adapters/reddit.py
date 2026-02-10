"""Reddit adapter for unified dashboard (stub)."""

from .base import PlatformAdapter, AccountMetrics, ContentItem


class RedditAdapter(PlatformAdapter):
    """Reddit API adapter.

    TODO: Implement with Reddit API (PRAW)
    - Use praw library for Reddit API
    - Fetch post/comment karma and engagement
    - Track subreddit-specific metrics
    """

    PLATFORM_NAME = "reddit"
    PLATFORM_COLOR = "#FF4500"

    def authenticate(self) -> bool:
        """Authenticate with Reddit API."""
        print(f"[Reddit] Authentication not yet implemented")
        return False

    def fetch_metrics(self, niche: str, days: int = 14) -> AccountMetrics:
        """Fetch Reddit account metrics."""
        return AccountMetrics(
            platform=self.PLATFORM_NAME,
            niche=niche,
            account_name=self.account_name,
            days=days,
            error="Reddit adapter not yet implemented",
        )

    def fetch_content_items(self, days: int = 14) -> list[ContentItem]:
        """Fetch Reddit posts."""
        return []
