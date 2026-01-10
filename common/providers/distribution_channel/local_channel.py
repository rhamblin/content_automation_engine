from common.app_logger import AppLogger
from common.contracts import IDistributionChannel
from common.contracts.messages.local_message import LocalMessage

class LocalDistributionChannel(IDistributionChannel):
    def __init__(self):
        self.logger = AppLogger(__name__)

    def provider_name(self) -> str:
        return "LocalDistributionChannel"
    
    def publish(self, title: str, description: str, image_url: str, **kwargs) -> bool:
        self.logger.info(f"Local Channel Publish Called with title: {title}, description: {description}, image_url: {image_url}, extra: {kwargs}")
        return True