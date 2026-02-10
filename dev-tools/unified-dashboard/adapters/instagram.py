"""Instagram adapter for unified dashboard (stub)."""

from .base import PlatformAdapter, AccountMetrics, ContentItem


class InstagramAdapter(PlatformAdapter):
    """Instagram API adapter (Meta Graph API).

    TODO: Implement with Meta Graph API
    - Requires Facebook Business account
    - Use /me/accounts to get Instagram Business Account ID
    - Use /{ig-user-id}/insights for account metrics
    - Use /{ig-media-id}/insights for post metrics
    """

    PLATFORM_NAME = "instagram"
    PLATFORM_COLOR = "#E1306C"

    def authenticate(self) -> bool:
        """Authenticate with Meta Graph API."""
        # TODO: Implement OAuth flow for Meta Graph API
        print(f"[Instagram] Authentication not yet implemented")
        return False

    def fetch_metrics(self, niche: str, days: int = 14) -> AccountMetrics:
        """Fetch Instagram account metrics."""
        return AccountMetrics(
            platform=self.PLATFORM_NAME,
            niche=niche,
            account_name=self.account_name,
            days=days,
            error="Instagram adapter not yet implemented",
        )

    def fetch_content_items(self, days: int = 14) -> list[ContentItem]:
        """Fetch Instagram posts/reels."""
        return []
