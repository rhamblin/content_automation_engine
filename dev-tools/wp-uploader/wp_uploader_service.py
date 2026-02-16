"""WP-uploader business logic — no file I/O."""

from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel

from models import WpUploadResult

logger = AppLogger(__name__)


class WpUploaderService:
    """Pure transform: topic row → generated content → published post result."""

    def __init__(self, wp: WordPressChannel):
        self.wp = wp

    def upload_topic(
        self,
        keyword: str,
        niche: str,
        image_url: str,
        media_id: int | None,
        status: str = "draft",
    ) -> WpUploadResult:
        """Generate content via LLM and publish to WordPress."""
        content = self.wp.render_content(
            source=None,
            text_data={
                "niche": niche,
                "keyword": keyword,
                "image_url": image_url,
            },
        )
        logger.info("Content generated")

        tags = [keyword]
        result = self.wp.publish(
            title=content.get("title", "Untitled"),
            content=content.get("content", ""),
            media_id=media_id,
            status=status,
            tags=tags,
        )

        return WpUploadResult(
            keyword=keyword,
            niche=niche,
            post_id=result["post_id"],
            url=result["url"],
            status=result["status"],
        )
