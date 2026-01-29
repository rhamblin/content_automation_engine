from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel, ITextProvider


class LocalTextProvider(ITextProvider):
    PROVIDER_NAME = "LocalTextProvider"

    def __init__(self):
        self.logger = AppLogger(__name__)

    def generate_text(
        self, niche: str, keyword: str, channel: IDistributionChannel
    ) -> dict:
        self.logger.info(
            f"Generating text for niche: {niche}, keyword: {keyword}, channel: {channel.PROVIDER_NAME}"
        )
        return {
            "title": f"Local Title for {keyword} in {niche}",
            "description": f"This is a local description about {keyword} in the niche of {niche}.",
        }
