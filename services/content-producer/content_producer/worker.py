import asyncio

from common.app_logger import AppLogger
from common.contracts.messages import ContentGenerationRequested, ContentReadyForStyling
from common.providers import registry
from common.repositories.cross_tenant import ChannelRepository
from common.repositories.tenant_scoped import (
    ContentRepository,
    IntegrationProfileRepository,
    NicheRepository,
)


class ContentProducerWorker:
    """Content Producer Worker - generates content for integration profiles"""

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

                if not incoming_msg:
                    continue

                tenant_id, integration_profile_id = (
                    incoming_msg.tenant_id,
                    incoming_msg.integration_profile_id,
                )

                self.logger.info(
                    f"Received ContentGenerationRequested: tenant={tenant_id}, "
                    f"integration_profile={integration_profile_id}"
                )

                outgoing_msgs: list[ContentReadyForStyling] = (
                    await self.__process_content_generation(
                        tenant_id, integration_profile_id
                    )
                )

                for msg in outgoing_msgs:
                    msg.chain_from(incoming_msg)
                    await self.registry.get_message_broker().publish(msg)
                    self.logger.info(f"\n\nPublished message: {msg}")

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def __process_content_generation(
        self, tenant_id, integration_profile_id
    ) -> list[ContentReadyForStyling]:
        """Process content generation for an integration profile"""

        async with self.registry.get_database().get_session() as session:
            profile_repo = IntegrationProfileRepository(session, tenant_id)
            niche_repo = NicheRepository(session, tenant_id)
            content_repo = ContentRepository(session, tenant_id)
            channel_repo = ChannelRepository(session)

            profile = await profile_repo.get_by_id(integration_profile_id)
            niche = await niche_repo.get_by_id_with_keywords(profile.niche_id)
            channel_entity = await channel_repo.get_by_id(profile.channel_id)
            distribution_channel = self.registry.get_channel(channel_entity.identifier)

            outgoing_msgs = []
            text_provider = self.registry.get_text_provider()

            for keyword in niche.keywords:
                try:
                    generated = text_provider.generate_text(
                        niche.title, keyword.term, distribution_channel
                    )

                    content = await content_repo.add(
                        niche_id=niche.external_id,
                        keyword_id=keyword.external_id,
                        title=generated.get("title", "[Untitled]"),
                        description=generated.get("description", "[No description]"),
                    )

                    input_image_uri = self.registry.get_blob_storage().fetch_image_uri(
                        keyword
                    )

                    await session.commit()

                    outgoing_msgs.append(
                        ContentReadyForStyling(
                            tenant_id=tenant_id,
                            keyword_id=str(keyword.external_id),
                            niche_id=str(niche.external_id),
                            channel_id=str(profile.channel_id),
                            content_id=str(content.external_id),
                            input_image_uri=input_image_uri,
                        )
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error generating content for keyword '{keyword.term}': {e}"
                    )

            return outgoing_msgs

    def __get_logger(self):
        return AppLogger(__name__)
