from .base import PlatformAdapter, AccountMetrics
from .pinterest import PinterestAdapter
from .instagram import InstagramAdapter
from .tiktok import TikTokAdapter
from .reddit import RedditAdapter

ADAPTERS = {
    "pinterest": PinterestAdapter,
    "instagram": InstagramAdapter,
    "tiktok": TikTokAdapter,
    "reddit": RedditAdapter,
}

__all__ = [
    "PlatformAdapter",
    "AccountMetrics",
    "PinterestAdapter",
    "InstagramAdapter",
    "TikTokAdapter",
    "RedditAdapter",
    "ADAPTERS",
]
