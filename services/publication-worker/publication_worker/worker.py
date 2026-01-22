import asyncio

from common.app_logger import AppLogger
from common.contracts.messages import ContentReadyForPublication
from common.providers import registry


class PublicationWorker:
    """Publication Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("PublicationWorker started.")

        while True:
            try:
                incoming_msg: (
                    ContentReadyForPublication
                ) = await self.registry.get_message_broker().consume(
                    ContentReadyForPublication
                )

                if incoming_msg:
                    self.logger.info("zzReceived Message!")

                    tenant_id = incoming_msg.tenant_id

                    # do work here to publish content

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
