from typing import Any

from common.app_logger import AppLogger
from common.contracts.interfaces import IDistributionChannel


class LocalDistributionChannel(IDistributionChannel):
    PROVIDER_NAME = "LocalDistributionChannel"

    def __init__(self):
        self.logger = AppLogger(__name__)

    @property
    def system_prompt(self) -> str:
        return "SYSTEM PROMPT"

    def render_content(self, source: Any, text_data: dict) -> Any:
        """Pass through - local channel doesn't render."""
        return text_data.get("content", "")

    def publish(self, title: str, description: str, content: Any, **kwargs) -> dict:
        self.logger.info(
            f"Local Channel Publish Called with title: {title}, content: {content}..., image_url: {image_url}, extra: {kwargs}"
        )
        import uuid

        return {
            "post_id": f"local_{uuid.uuid4().hex[:12]}",
            "url": f"http://localhost/pin/local_{uuid.uuid4().hex[:12]}",
            "status": "published",
        }
