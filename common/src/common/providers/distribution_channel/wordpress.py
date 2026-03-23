from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel, ILLMProvider
from common.contracts.models import CanvasSpec, VisualStyle


class WordPressChannel(IDistributionChannel):
    """WordPress distribution channel via REST API.

    Raises:
        ConnectionError: When WordPress API is unreachable.
        RuntimeError: When WordPress API returns an error response.
        ValueError: When response data is invalid or missing required fields.
    """

    def __init__(
        self,
        site_url: str,
        username: str,
        app_password: str,
        llm: ILLMProvider,
        amazon_tag: str = "",
        prompt_override: str = "",
    ):
        self.logger = AppLogger(__name__)
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.api_url = f"{self.site_url}/wp-json/wp/v2/posts"
        self.llm = llm
        self.amazon_tag = amazon_tag
        self.prompt_override = prompt_override

    @property
    def provider_name(self) -> str:
        return "wordpress"

    @property
    def canvas(self) -> CanvasSpec | None:
        return None

    @property
    def styles(self) -> dict[str, VisualStyle]:
        return {}

    @property
    def system_prompt(self) -> str:
        if not self.prompt_override:
            raise ValueError("No channel prompt configured for wordpress")
        return self.prompt_override.replace("{amazon_tag}", self.amazon_tag)

    def render_content(self, source: Any, text_data: dict, style=None, **kwargs) -> dict:
        """Render WordPress content via LLM provider.

        Args:
            source: Not used for WordPress (pass None)
            text_data: Dict with niche, keyword, image_url, persona, locale
            style: Optional VisualStyle for field schema
            **kwargs: Forwarded to LLM generate (persona_prompt, audience_prompt)

        Returns:
            Dict with title, content (HTML), etc.
        """
        return self.llm.generate(
            niche=text_data.get("niche", ""),
            keyword=text_data.get("keyword", ""),
            channel=self,
            persona=text_data.get("persona"),
            style=style,
            locale=text_data.get("locale", "en"),
            image_url=text_data.get("image_url", ""),
            intent=text_data.get("intent", "informational"),
            amazon_monetization_angle=text_data.get("amazon_monetization_angle", ""),
            **kwargs,
        )

    def _get_or_create_tags(self, tag_names: list[str]) -> list[int]:
        """Get or create WordPress tags by name, return list of tag IDs."""
        auth = HTTPBasicAuth(self.username, self.app_password)
        tags_url = f"{self.site_url}/wp-json/wp/v2/tags"
        tag_ids = []

        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            try:
                # Search for existing tag
                resp = requests.get(tags_url, params={"search": name}, auth=auth, timeout=10)
                if resp.ok and resp.json():
                    for tag in resp.json():
                        if tag["name"].lower() == name.lower():
                            tag_ids.append(tag["id"])
                            break
                    else:
                        # Exact match not found, create it
                        resp = requests.post(tags_url, json={"name": name}, auth=auth, timeout=10)
                        if resp.ok:
                            tag_ids.append(resp.json()["id"])
                else:
                    # No results, create tag
                    resp = requests.post(tags_url, json={"name": name}, auth=auth, timeout=10)
                    if resp.ok:
                        tag_ids.append(resp.json()["id"])
            except requests.RequestException:
                self.logger.warning(f"Failed to create/find tag: {name}")

        return tag_ids

    def upload_media(self, image_path: str) -> tuple[int, str]:
        """Upload a local image file to the WordPress media library.

        Args:
            image_path: Absolute path to the image file.

        Returns:
            (media_id, source_url) of the newly created media item.

        Raises:
            FileNotFoundError: When image_path does not exist.
            ConnectionError: When WordPress API is unreachable.
            RuntimeError: When WordPress API returns an error response.
        """
        from pathlib import Path

        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        content_type = content_types.get(path.suffix.lower(), "image/jpeg")

        media_url = f"{self.site_url}/wp-json/wp/v2/media"
        auth = HTTPBasicAuth(self.username, self.app_password)

        try:
            resp = requests.post(
                media_url,
                headers={
                    "Content-Disposition": f'attachment; filename="{path.name}"',
                    "Content-Type": content_type,
                },
                data=path.read_bytes(),
                auth=auth,
                timeout=60,
            )
        except requests.RequestException as e:
            raise ConnectionError(f"WordPress media upload failed: {e}") from e

        if resp.status_code >= 400:
            raise RuntimeError(
                f"WordPress media upload error: {resp.status_code} - {resp.text}"
            )

        data = resp.json()
        media_id = data["id"]
        source_url = data.get("source_url", "")
        self.logger.info("Uploaded media id=%s url=%s", media_id, source_url)
        return media_id, source_url

    def publish(
        self,
        title: str,
        content: str,
        media_id: int | None = None,
        status: str = "draft",
        tags: list[str] | None = None,
    ) -> dict:
        """Publish content to WordPress."""
        post_data: dict = {
            "title": title,
            "content": content,
            "status": status,
        }

        if media_id:
            post_data["featured_media"] = media_id

        if tags:
            tag_ids = self._get_or_create_tags(tags)
            if tag_ids:
                post_data["tags"] = tag_ids

        self.logger.info(f"Publishing to WordPress: {title}")

        try:
            response = requests.post(
                self.api_url,
                json=post_data,
                auth=HTTPBasicAuth(self.username, self.app_password),
                timeout=30,
            )
        except requests.RequestException as e:
            raise ConnectionError(f"WordPress API unreachable: {e}") from e

        if response.status_code >= 400:
            raise RuntimeError(
                f"WordPress API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        if "id" not in data:
            raise ValueError("WordPress response missing post ID")

        return {
            "post_id": str(data["id"]),
            "url": data.get("link", ""),
            "status": data.get("status", "unknown"),
        }
