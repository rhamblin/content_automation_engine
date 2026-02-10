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

    @staticmethod
    def build_pin_maker_prompt(style_brief: str) -> str:
        """Build prompt for pin maker with style selection."""
        return f"""
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

    def __init__(self, prompt: str | None = None):
        self.logger = AppLogger(__name__)
        self._prompt = prompt

    @property
    def system_prompt(self) -> str:
        return self._prompt if self._prompt else self.DEFAULT_PROMPT

    def publish(self, title: str, content: str, image_url: str, **kwargs) -> dict:
        """Publish content to Pinterest.

        Raises:
            ConnectionError: When Pinterest API is unreachable.
            RuntimeError: When Pinterest API returns an error response.
            ValueError: When response is missing required fields.
        """
        hashtags = kwargs.get("hashtags", [])
        self.logger.info(f"Publishing to Pinterest: {title} - {image_url} - {hashtags}")

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
