from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel, ILLMProvider


class LocalLLMProvider(ILLMProvider):
    PROVIDER_NAME = "local"

    def __init__(self):
        self.logger = AppLogger(__name__)

    def generate(
        self, niche: str, keyword: str, channel: IDistributionChannel, persona=None, style=None, locale: str = "en", **kwargs
    ) -> dict:
        self.logger.info(
            f"Generating for niche: {niche}, keyword: {keyword}, channel: {channel.PROVIDER_NAME}, locale: {locale}"
        )

        # If style provided, return only fields defined in style
        if style:
            result = {}
            for field in style.text_fields():
                result[field] = f"Local {field} for {keyword}"
            return result

        return {
            "title": f"Local Title for {keyword} in {niche}",
            "content": f"This is local content about {keyword} in the niche of {niche}.",
        }
