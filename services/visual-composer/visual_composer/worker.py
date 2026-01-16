import asyncio

from common.app_logger import AppLogger
from common.contracts import ContentReadyForStyling
from common.contracts.messages.content_ready_for_publication import (
    ContentReadyForPublication,
)
from common.providers import registry


class VisualComposerWorker:
    """Visual Composer Worker"""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop"""
        self.logger.info("VisualComposerWorker started.")

        while True:
            try:
                incoming_msg: (
                    ContentReadyForStyling
                ) = await self.registry.get_message_broker().consume(
                    ContentReadyForStyling
                )

                if incoming_msg:
                    tenant_id = incoming_msg.tenant_id

                # do work here to compose visuals

                outgoing_msg = ContentReadyForPublication(
                    tenant_id=tenant_id,
                    keyword_id="",
                    niche_id="",
                    channel_id="",
                    content_id="",
                    rendered_image_id="",
                ).chain_from(incoming_msg)

                await self.registry.get_message_broker().publish(outgoing_msg)

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    def __get_logger(self):
        return AppLogger(__name__)
