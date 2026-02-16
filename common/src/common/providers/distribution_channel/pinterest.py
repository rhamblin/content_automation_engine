from typing import Any

import requests
from PIL import Image
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel
from common.contracts.models import CanvasSpec
from common.rendering import render_image

PINTEREST_CANVAS = CanvasSpec(width=1000, height=1500, format="RGB")

class PinterestChannel(IDistributionChannel):
    """Pinterest distribution channel.

    Raises:
        ConnectionError: When Pinterest API is unreachable.
        RuntimeError: When Pinterest API returns an error response.
        ValueError: When response data is invalid or missing required fields.
    """

    DEFAULT_PROMPT = """
You are a Pinterest marketing expert creating high-engagement Pins that drive clicks, saves, and shares.
You understand Pinterest user behavior: aesthetics, aspirations, seasonal intent, and discovery mindset.
You apply Pinterest SEO best practices with high-intent keywords and power words.

GOALS:
1. Craft scroll-stopping titles that maximize click-through rate on mobile.
2. Write benefit-driven descriptions that encourage saves and shares.
3. All text must render cleanly on images - short, punchy, no special characters.

STRICT OUTPUT RULES:
- Output ONLY valid JSON, no markdown, no explanations
- NEVER use emoji, unicode symbols, or special characters in any field
- All text must be plain text (no emoji/unicode symbols) - it will be rendered directly onto images
- Keep titles short (2-4 words) so they fit on one line at large font sizes
"""

    PINTEREST_API_BASE = "https://api.pinterest.com/v5"

    def __init__(self, prompt_override: str = "", access_token: str = ""):
        """Initialize Pinterest channel."""
        self.logger = AppLogger(__name__)
        self.prompt_override = prompt_override
        self.access_token = access_token

    @property
    def provider_name(self) -> str:
        return "pinterest"

    @property
    def system_prompt(self) -> str:
        return self.prompt_override if self.prompt_override else self.DEFAULT_PROMPT

    @property
    def canvas(self) -> CanvasSpec:
        return PINTEREST_CANVAS

    def render_content(
        self,
        source: Image.Image,
        text_data: dict,
        style: Any = None,
        brand_text: str = "",
        width: int = 1000,
        height: int = 1500,
    ) -> Image.Image:
        """Render Pinterest pin image.

        Args:
            source: Source PIL Image
            text_data: Text data (title, tagline, style, etc.)
            style: VisualStyle object with text elements and overlay
            brand_text: Brand watermark text
            width: Output width (default 1000)
            height: Output height (default 1500)

        Returns:
            PIL Image with text overlay
        """
        if width != PINTEREST_CANVAS.width or height != PINTEREST_CANVAS.height:
            canvas = CanvasSpec(width=width, height=height)
        else:
            canvas = PINTEREST_CANVAS

        return render_image(source, canvas, style, text_data, brand_text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, RuntimeError)),
        reraise=True,
    )
    def create_board(self, name: str, privacy: str = "SECRET") -> dict:
        """POST /v5/boards — create a board.

        Returns:
            dict with keys: board_id, url

        Raises:
            ConnectionError: When Pinterest API is unreachable.
            RuntimeError: When Pinterest API returns an error response.
        """
        try:
            resp = requests.post(
                f"{self.PINTEREST_API_BASE}/boards",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={"name": name, "privacy": privacy},
                timeout=30,
            )
        except requests.ConnectionError as e:
            raise ConnectionError(f"Pinterest API unreachable: {e}") from e

        if resp.status_code == 429 or resp.status_code >= 500:
            raise RuntimeError(f"Pinterest API {resp.status_code}: {resp.text}")
        if not resp.ok:
            raise RuntimeError(f"Pinterest API {resp.status_code}: {resp.text}")

        data = resp.json()
        return {
            "board_id": data.get("id"),
            "url": f"https://pinterest.com/board/{data.get('id')}",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, RuntimeError)),
        reraise=True,
    )
    def create_pin(
        self,
        board_id: str,
        image_b64: str,
        content_type: str,
        title: str,
        description: str,
        link: str | None = None,
        alt_text: str | None = None,
    ) -> dict:
        """POST /v5/pins with base64 image.

        Returns:
            dict with keys: post_id, url, status

        Raises:
            ConnectionError: When Pinterest API is unreachable.
            RuntimeError: When Pinterest API returns an error response (4xx/5xx).
        """
        payload: dict[str, Any] = {
            "board_id": board_id,
            "title": title,
            "description": description,
            "media_source": {
                "source_type": "image_base64",
                "content_type": content_type,
                "data": image_b64,
            },
        }
        if link:
            payload["link"] = link
        if alt_text:
            payload["alt_text"] = alt_text

        try:
            resp = requests.post(
                f"{self.PINTEREST_API_BASE}/pins",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
        except requests.ConnectionError as e:
            raise ConnectionError(f"Pinterest API unreachable: {e}") from e

        if resp.status_code == 429 or resp.status_code >= 500:
            raise RuntimeError(f"Pinterest API {resp.status_code}: {resp.text}")
        if not resp.ok:
            raise RuntimeError(f"Pinterest API {resp.status_code}: {resp.text}")

        data = resp.json()
        return {
            "post_id": data.get("id"),
            "url": f"https://pinterest.com/pin/{data.get('id')}",
            "status": "published",
        }

    def publish(self, title: str, description: str, content: Any, **kwargs) -> dict:
        """Publish content to Pinterest.

        Args:
            title: Pin title
            description: Pin description
            content: Base64-encoded image string

        Raises:
            ConnectionError: When Pinterest API is unreachable.
            RuntimeError: When Pinterest API returns an error response.
        """
        return self.create_pin(
            board_id=kwargs["board_id"],
            image_b64=content,
            content_type=kwargs.get("content_type", "image/jpeg"),
            title=title,
            description=description,
            link=kwargs.get("link"),
            alt_text=kwargs.get("alt_text"),
        )
