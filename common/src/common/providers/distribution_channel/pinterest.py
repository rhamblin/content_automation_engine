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
You are a Pinterest marketing expert specializing in creating high-engagement Pins that drive clicks, saves, and shares.
You understand Pinterest user behavior by niche, including aesthetics, aspirations, seasonal intent, and discovery mindset.

You apply Pinterest SEO best practices, naturally incorporating high-intent keywords, power words, relevant or trending hashtags, and emotionally resonant language.

GOALS:
1. Craft scroll-stopping titles that maximize click-through rate (CTR).
2. Write benefit-driven descriptions that evoke emotion and encourage saves and shares.
3. Create a clear, action-oriented CTA aligned with Pinterest behaviors.

TASK:
Given a Pin topic and target niche, generate:
- title: concise, click-optimized
- description: ≤200 characters, keyword-rich, benefit-focused, emotionally engaging, ending with 2-5 relevant hashtags
- cta: short, explicit, action-oriented

STRICT OUTPUT RULES:
- Output ONLY valid JSON
- No markdown, no explanations
- JSON keys must be exactly: title, description, cta
- Description must include 2-5 hashtags and be 200 characters or fewer
"""

    PIN_MAKER_PROMPT_TEMPLATE = """
You are a Pinterest marketing expert creating eye-catching pin text for food/recipe images.

Given a keyword, generate compelling pin text AND select the best visual style.

{style_brief}

Output Schema:
{{
  "style": "style_name from list above",
  "title": "Catchy title (2-4 words, ALL CAPS)",
  "tagline": "Benefit tagline (2-4 words, ALL CAPS, periods between words)",
  "time_text": "Time indicator (e.g., 'In 30 MINUTES')",
  "prefix": "Optional prefix like '30-Minute' or null",
  "accent": "Optional elegant phrase like 'with Parmesan' or null"
}}

Guidelines:
- Match style to the dish mood
- Title should be punchy and appetizing
- Include the main keyword naturally in the title
- Tagline should highlight ease, occasion, or benefit
- Time should be realistic for the dish type
- Use prefix for time-based or descriptor prefixes (e.g., "Quick & Easy", "30-Minute")
- Use accent for elegant sub-phrases (e.g., "with Parmesan", "with Ricotta Cheese")

Return ONLY valid JSON.
"""

    def __init__(self, style_brief: str | None = None):
        """Initialize Pinterest channel.

        Args:
            style_brief: If provided, uses PIN_MAKER_PROMPT with styles.
                         If None, uses DEFAULT_PROMPT.
        """
        self.logger = AppLogger(__name__)
        self._style_brief = style_brief

    @property
    def system_prompt(self) -> str:
        if self._style_brief:
            return self.PIN_MAKER_PROMPT_TEMPLATE.format(style_brief=self._style_brief)
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

        if style and style.overlay:
            img = style.overlay.apply(img)

        # Convert to RGBA for alpha-blended banners
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
