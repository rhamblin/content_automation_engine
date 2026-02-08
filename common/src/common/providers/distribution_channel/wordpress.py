import requests
from requests.auth import HTTPBasicAuth

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel


class WordPressChannel(IDistributionChannel):
    """WordPress distribution channel via REST API.

    Raises:
        ConnectionError: When WordPress API is unreachable.
        RuntimeError: When WordPress API returns an error response.
        ValueError: When response data is invalid or missing required fields.
    """

    PROVIDER_NAME = "wordpress"

    def __init__(
        self,
        site_url: str,
        username: str,
        app_password: str,
        system_prompt: str,
    ):
        self.logger = AppLogger(__name__)
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.api_url = f"{self.site_url}/wp-json/wp/v2/posts"
        self._system_prompt = system_prompt

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def publish(
        self,
        title: str,
        content: str,
        media_id: int | None = None,
        status: str = "draft",
    ) -> dict:
        """Publish content to WordPress."""
        post_data: dict = {
            "title": title,
            "content": content,
            "status": status,
        }

        if media_id:
            post_data["featured_media"] = media_id

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
