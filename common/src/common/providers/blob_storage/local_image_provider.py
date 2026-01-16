from common.app_logger import AppLogger
from common.contracts.interfaces.image_provider import IBlobStorage


class LocalImageProvider(IBlobStorage):
    PROVIDER_NAME = "LocalImageProvider"

    def __init__(self):
        self.logger = AppLogger(__name__)

    def fetch_image(self, keyword: str) -> str:
        return f"https://local.images/{keyword}.jpg"
