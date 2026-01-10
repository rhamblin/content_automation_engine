from common.app_logger import AppLogger
from common.contracts.text_provider import ITextProvider

class LocalTextProvider(ITextProvider):
    def __init__(self):
        self.logger = AppLogger(__name__)

    def provider_name(self) -> str:
        return "LocalTextProvider"
    
    def generate_text(self, niche: str, keyword: str, channel: str) -> dict:
        self.logger.info(f"Generating text for niche: {niche}, keyword: {keyword}, channel: {channel}")
        return {
            "title": f"Local Title for {keyword} in {niche}",
            "description": f"This is a local description about {keyword} in the niche of {niche} for the {channel} channel."
        }