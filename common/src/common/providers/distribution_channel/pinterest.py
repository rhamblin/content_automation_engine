from typing import Any

from PIL import Image, ImageDraw

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel


class PinterestChannel(IDistributionChannel):
    """Pinterest distribution channel.

    Raises:
        ConnectionError: When Pinterest API is unreachable.
        RuntimeError: When Pinterest API returns an error response.
        ValueError: When response data is invalid or missing required fields.
    """

    PROVIDER_NAME = "pinterest"

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
- All text must be plain ASCII - it will be rendered directly onto images
- Keep titles short (2-4 words) so they fit on one line at large font sizes
"""

    def __init__(self):
        """Initialize Pinterest channel."""
        self.logger = AppLogger(__name__)

    @property
    def system_prompt(self) -> str:
        return self.DEFAULT_PROMPT

    def _smart_crop_resize(
        self, img: Image.Image, target_w: int, target_h: int
    ) -> Image.Image:
        """Resize and crop image to target dimensions."""
        orig_w, orig_h = img.size
        target_ratio = target_w / target_h
        orig_ratio = orig_w / orig_h

        if orig_ratio > target_ratio:
            new_w = int(orig_h * target_ratio)
            left = (orig_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, orig_h))
        else:
            new_h = int(orig_w / target_ratio)
            top = (orig_h - new_h) // 3
            img = img.crop((0, top, orig_w, top + new_h))

        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)

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
        img = self._smart_crop_resize(source, width, height)

        if style and style.overlays:
            for overlay in style.overlays:
                img = overlay.apply(img)

        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        if style:
            for key, element in style.elements():
                text = brand_text if key == "watermark" else text_data.get(key)
                if text:
                    result = element.draw(draw, text, img.width, img.height, base_img=img)
                    if result is not None:
                        img = result
                        draw = ImageDraw.Draw(img)

        return img.convert("RGB")

    def publish(self, title: str, description: str, content: Any, **kwargs) -> dict:
        """Publish content to Pinterest.

        Raises:
            ConnectionError: When Pinterest API is unreachable.
            RuntimeError: When Pinterest API returns an error response.
            ValueError: When response is missing required fields.
        """
        hashtags = kwargs.get("hashtags", [])
        self.logger.info(f"Publishing to Pinterest: {title} - {hashtags}")

        # TODO: Implement actual Pinterest API call
        # When implemented, wrap API calls like:
        # try:
        #     response = pinterest_api.create_pin(...)
        # except requests.RequestException as e:
        #     raise ConnectionError(f"Pinterest API unreachable: {e}") from e
        #
        # if response.status_code >= 400:
        #     raise RuntimeError(f"Pinterest API error: {response.status_code}")
        #
        # if "id" not in response.json():
        #     raise ValueError("Pinterest response missing pin ID")

        return {
            "post_id": "mock_pin_id_123456",
            "url": "https://pinterest.com/pin/mock_pin_id_123456",
            "status": "published",
        }
