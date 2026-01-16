import asyncio

from common.app_logger import AppLogger
from common.providers import registry


class ManagementApiWorker:
    """Management API Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("ManagementApiWorker started.")

        while True:
            try:
                # Implement management API tasks here
                pass
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
