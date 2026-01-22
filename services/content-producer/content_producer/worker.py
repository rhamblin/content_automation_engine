import asyncio

from common.app_logger import AppLogger
from common.contracts.messages import ContentGenerationRequested, ContentReadyForStyling
from common.providers import registry


class ContentProducerWorker:
    """Content Producer Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("ContentProducerWorker started.")

        while True:
            try:
                incoming_msg: (
                    ContentGenerationRequested
                ) = await self.registry.get_message_broker().consume(
                    ContentGenerationRequested
                )

                if incoming_msg:
                    self.logger.info("zzReceived Message!")

                    tenant_id = incoming_msg.tenant_id

                    # do work here to produce content

                    outgoing_msg = ContentReadyForStyling(
                        tenant_id=tenant_id,
                        keyword_id="",
                        niche_id="",
                        channel_id="",
                        content_id="",
                        base_image_id="",
                    ).chain_from(incoming_msg)

                    await self.registry.get_message_broker().publish(outgoing_msg)
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
