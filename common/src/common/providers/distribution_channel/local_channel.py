from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel

class LocalDistributionChannel(IDistributionChannel):
    PROVIDER_NAME = "LocalDistributionChannel"

    def __init__(self):
        self.logger = AppLogger(__name__)
    
    def publish(self, title: str, description: str, image_url: str, **kwargs) -> bool:
        self.logger.info(f"Local Channel Publish Called with title: {title}, description: {description}, image_url: {image_url}, extra: {kwargs}")
        return True