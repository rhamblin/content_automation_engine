from common.app_logger import AppLogger
from common.contracts.image_provider import IImageProvider

class LocalImageProvider(IImageProvider):
    def __init__(self):
        self.logger = AppLogger(__name__)


    def provider_name(cls) -> str:
        return "LocalImageProvider"
    
    def fetch_image(self, keyword: str) -> str:
        return f"https://local.images/{keyword}.jpg"