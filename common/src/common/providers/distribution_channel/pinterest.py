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

    def __init__(self):
        self.logger = AppLogger(__name__)

    @property
    def system_prompt(self) -> str:
        return """
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

    def publish(self, title: str, description: str, image_url: str, **kwargs) -> dict:
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
