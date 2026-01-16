import asyncio

from common.app_logger import AppLogger
from common.contracts import ContentReadyForPublication
from common.contracts.messages.content_ready_for_styling import ContentReadyForStyling
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
                    tenant_id = incoming_msg.tenant_id

                    # do work here to publish content

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
