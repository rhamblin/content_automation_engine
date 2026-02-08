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

    def __init__(self, site_url: str, username: str, app_password: str):
        self.logger = AppLogger(__name__)
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password
        self.api_url = f"{self.site_url}/wp-json/wp/v2/posts"

    @property
    def system_prompt(self) -> str:
        return """
            You are a WordPress content expert specializing in creating SEO-optimized blog posts that drive organic traffic and engagement.
            You understand content marketing best practices, including keyword placement, readability, and user intent.

            You apply WordPress SEO best practices, naturally incorporating target keywords, using proper heading structure, and creating scannable content.

            GOALS:
            1. Craft compelling titles that maximize click-through rate from search results.
            2. Write engaging, informative content that provides value to readers.
            3. Structure content with clear headings and logical flow.

            TASK:
            Given a topic and target niche, generate:
            - title: SEO-optimized, compelling blog post title
            - content: Full blog post in HTML format with proper heading tags (h2, h3), paragraphs, and formatting. Aim for 500-800 words.
            - excerpt: A 150-160 character meta description for SEO

            STRICT OUTPUT RULES:
            - Output ONLY valid JSON
            - No markdown outside the JSON, no explanations
            - JSON keys must be exactly: title, content, excerpt
            - Content must be valid HTML suitable for WordPress
            """

    def publish(
        self, title: str, description: str, image_url: str = "", **kwargs
    ) -> dict:
        """Publish content to WordPress.

        Args:
            title: Post title
            description: Post content (HTML)
            image_url: Featured image URL (optional, not used directly)
            **kwargs: Additional fields (excerpt, status, categories, tags)

        Raises:
            ConnectionError: When WordPress API is unreachable.
            RuntimeError: When WordPress API returns an error response.
            ValueError: When response is missing required fields.
        """
        post_data = {
            "title": title,
            "content": description,
            "status": kwargs.get("status", "draft"),
        }

        if excerpt := kwargs.get("excerpt"):
            post_data["excerpt"] = excerpt

        if categories := kwargs.get("categories"):
            post_data["categories"] = categories

        if tags := kwargs.get("tags"):
            post_data["tags"] = tags

        if featured_media := kwargs.get("featured_media"):
            post_data["featured_media"] = featured_media

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
