"""WP-uploader business logic — no file I/O."""

import requests
from requests.auth import HTTPBasicAuth

from common.app_logger import AppLogger
from common.providers.distribution_channel.wordpress import WordPressChannel

from common.workflows.wp_uploader.wp_uploader_response import WpUploadResult

logger = AppLogger(__name__)


class WpUploaderService:
    """Pure transform: topic row → generated content → published post result."""

    def __init__(self, wp: WordPressChannel):
        self.wp = wp

    def resolve_media(
        self, keyword: str, site_url: str, username: str, app_password: str
    ) -> tuple[int | None, str]:
        """Search WP media library for an image matching *keyword*.

        Returns:
            (media_id, image_url) or (None, "") when no match found.
        """
        search_term = keyword.replace(" ", "_")
        try:
            resp = requests.get(
                f"{site_url}/wp-json/wp/v2/media",
                params={"search": search_term, "per_page": 10},
                auth=HTTPBasicAuth(username, app_password),
                timeout=10,
            )
        except requests.RequestException as e:
            logger.warning(f"Media lookup failed for '{keyword}': {e}")
            return None, ""

        if not resp.ok or not resp.json():
            return None, ""

        for media in resp.json():
            source_url = media.get("source_url", "")
            slug = media.get("slug", "")
            if search_term.lower() in source_url.lower() or search_term.lower() in slug.lower():
                return media["id"], source_url

        first = resp.json()[0]
        return first["id"], first.get("source_url", "")

    def upload_topic(
        self,
        keyword: str,
        niche: str,
        image_url: str,
        media_id: int | None,
        status: str = "draft",
        persona_prompt: str | None = None,
        copy_style_prompt: str | None = None,
        audience_prompt: str | None = None,
    ) -> WpUploadResult:
        """Generate content via LLM and publish to WordPress."""
        content = self.wp.render_content(
            source=None,
            text_data={
                "niche": niche,
                "keyword": keyword,
                "image_url": image_url,
            },
            persona_prompt=persona_prompt,
            copy_style_prompt=copy_style_prompt,
            audience_prompt=audience_prompt,
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
