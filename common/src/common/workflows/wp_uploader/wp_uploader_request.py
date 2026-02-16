"""WP-uploader input contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WpUploaderRequest:
    """Defines what wp-uploader accepts."""

    topics_file: str  # required — path to CSV with niche,keyword,image_url,media_id
    niche: str = "food"  # default niche (rows can override)
    status: str = "draft"  # draft | publish
