"""Base adapter class for platform integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DailyMetrics:
    """Daily metrics for a single day."""
    date: str
    impressions: int = 0
    engagements: int = 0  # likes, saves, comments combined
    clicks: int = 0
    reach: int = 0
    shares: int = 0
    saves: int = 0
    comments: int = 0
    spend: float = 0.0  # for paid


@dataclass
class ContentItem:
    """Individual content piece (pin, post, video, etc.)."""
    id: str
    title: str
    url: str
    created_at: str
    content_type: str  # pin, post, reel, video, etc.
    totals: dict = field(default_factory=dict)
    daily: list[DailyMetrics] = field(default_factory=list)


@dataclass
class AccountMetrics:
    """Aggregated metrics for an account."""
    platform: str
    niche: str
    account_name: str

    # Totals
    impressions: int = 0
    engagements: int = 0
    clicks: int = 0
    reach: int = 0
    followers: int = 0

    # Paid totals (if applicable)
    spend: float = 0.0
    paid_impressions: int = 0
    paid_clicks: int = 0

    # Daily aggregated data
    daily: list[DailyMetrics] = field(default_factory=list)

    # Content items
    content_items: list[ContentItem] = field(default_factory=list)

    # Campaigns (if applicable)
    campaigns: list[dict] = field(default_factory=list)

    # Metadata
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())
    days: int = 14
    error: str | None = None


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters."""

    PLATFORM_NAME: str = "unknown"
    PLATFORM_COLOR: str = "#666666"

    # Normalized metric names that all platforms should map to
    METRIC_MAP = {
        "impressions": "impressions",
        "engagements": "engagements",
        "clicks": "clicks",
        "reach": "reach",
        "saves": "saves",
        "shares": "shares",
        "comments": "comments",
    }

    def __init__(self, credentials_path: str, account_config: dict):
        self.credentials_path = credentials_path
        self.account_config = account_config
        self.account_name = account_config.get("name", "Unknown")

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the platform. Returns True if successful."""
        pass

    @abstractmethod
    def fetch_metrics(self, niche: str, days: int = 14) -> AccountMetrics:
        """Fetch metrics for the account."""
        pass

    @abstractmethod
    def fetch_content_items(self, days: int = 14) -> list[ContentItem]:
        """Fetch individual content items with their metrics."""
        pass

    def get_engagement_rate(self, metrics: AccountMetrics) -> float:
        """Calculate engagement rate."""
        if metrics.impressions == 0:
            return 0.0
        return (metrics.engagements / metrics.impressions) * 100

    def get_click_rate(self, metrics: AccountMetrics) -> float:
        """Calculate click-through rate."""
        if metrics.impressions == 0:
            return 0.0
        return (metrics.clicks / metrics.impressions) * 100
