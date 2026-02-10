"""TikTok adapter for unified dashboard (stub)."""

from .base import PlatformAdapter, AccountMetrics, ContentItem


class TikTokAdapter(PlatformAdapter):
    """TikTok API adapter.

    TODO: Implement with TikTok API
    - Requires TikTok for Developers account
    - Use Content Posting API for video data
    - Use TikTok for Business API for analytics
    """

    PLATFORM_NAME = "tiktok"
    PLATFORM_COLOR = "#000000"

    def authenticate(self) -> bool:
        """Authenticate with TikTok API."""
        print(f"[TikTok] Authentication not yet implemented")
        return False

    def fetch_metrics(self, niche: str, days: int = 14) -> AccountMetrics:
        """Fetch TikTok account metrics."""
        return AccountMetrics(
            platform=self.PLATFORM_NAME,
            niche=niche,
            account_name=self.account_name,
            days=days,
            error="TikTok adapter not yet implemented",
        )

    def fetch_content_items(self, days: int = 14) -> list[ContentItem]:
        """Fetch TikTok videos."""
        return []
