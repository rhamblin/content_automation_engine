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
from common.contracts.models import CanvasSpec, ImageOverlay, TextElement, VisualStyle
from common.rendering import render_image

PINTEREST_CANVAS = CanvasSpec(width=1000, height=1500, format="RGB")

STYLES: dict[str, VisualStyle] = {
    "ribbon_box": VisualStyle(
        name="ribbon_box",
        description="White card with red ribbon banner above a bold serif title and tagline. The ribbon holds a short descriptor, the card holds the main title and a supporting benefit phrase. Clean editorial look with strong contrast.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="#FFFFFF",
            outline_color="#FFFFFF",
            y_position=505,
            outline_width=1,
        ),
        title=TextElement(
            font_file="PlayfairDisplay.ttf",
            font_size=120,
            color="#1a1a1a",
            y_position=600,
            outline_width=0,
            max_width_pct=0.70,
            max_lines=2,
        ),
        watermark=TextElement(
            font_file="DancingScript.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#5C3A1E",
        ),
        overlays=[
            ImageOverlay(
                position="box",
                color="#FFFFFF",
                opacity=0.76,
                height_pct=0.35,
                y_position=700,
                width_pct=0.82,
                border_color="#cccccc",
                border_width=2,
            ),
            ImageOverlay(
                position="box",
                color="#d63031",
                opacity=0.77,
                height_pct=0.04,
                y_position=530,
                width_pct=0.45,
                shape="ribbon",
                notch_pct=0.04,
            ),
        ],
    ),
    "slab_script": VisualStyle(
        name="slab_script",
        description="Full-width cream band with bold brown slab-serif title and a warm script accent line below. The title is the hero, the accent adds an elegant detail like an ingredient or flavor note.",
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=110,
            color="#5C3A1E",
            y_position=620,
            outline_width=0,
            max_lines=1,
        ),
        accent=TextElement(
            font_file="DancingScript.ttf",
            font_size=72,
            color="#C2185B",
            y_position=740,
            outline_width=1,
            outline_color="#FFFFFF",
        ),
        watermark=TextElement(
            font_file="DancingScript.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#5C3A1E",
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.70,
                height_pct=0.22,
                y_position=710,
                border_color="#5C3A1E",
                border_width=3,
            ),
        ],
    ),
    "bold_band": VisualStyle(
        name="bold_band",
        description="Full-width white band with gold border lines, massive bold title in the center, an uppercase prefix above and a tagline below. Prefix is a short label, tagline highlights a benefit or occasion.",
        prefix=TextElement(
            font_file="Montserrat.ttf",
            font_size=38,
            color="#3D4A1A",
            y_position=640,
            outline_width=1,
        ),
        title=TextElement(
            font_file="BebasNeue.ttf",
            font_size=140,
            color="#1a1a1a",
            y_position=700,
            outline_width=0,
            max_lines=1,
        ),
        tagline=TextElement(
            font_file="Montserrat.ttf",
            font_size=36,
            color="#3D4A1A",
            y_position=850,
            outline_width=1,
        ),
        watermark=TextElement(
            font_file="DancingScript.ttf",
            font_size=48,
            color="#FFFFFF",
            y_position=-60,
            alignment="right",
            outline_width=2,
            outline_color="#5C3A1E",
        ),
        overlays=[
            ImageOverlay(
                position="center",
                color="#FFFFFF",
                opacity=0.95,
                height_pct=0.24,
                y_position=750,
                border_color="#9B8C4E",
                border_width=4,
            ),
        ],
    ),
}


def get_style(name: str) -> VisualStyle:
    """Get a style by name."""
    if name not in STYLES:
        raise KeyError(f"Style '{name}' not found. Available: {list(STYLES.keys())}")
    return STYLES[name]


def get_style_brief() -> str:
    """Generate style options for LLM prompt."""
    lines = ["Available styles:"]
    for name, style in STYLES.items():
        lines.append(f'- "{name}": {style.description}')
    return "\n".join(lines)


def list_styles() -> list[str]:
    """Return available style names."""
    return list(STYLES.keys())


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

    @property
    def styles(self) -> dict[str, VisualStyle]:
        return STYLES

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
