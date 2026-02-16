"""WP-uploader output contract."""

from dataclasses import dataclass


@dataclass
class WpUploadResult:
    """Result of uploading a single post."""

    keyword: str
    niche: str
    post_id: int | None = None
    url: str | None = None
    status: str | None = None
    error: str | None = None
