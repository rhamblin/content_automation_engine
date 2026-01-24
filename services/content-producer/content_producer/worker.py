import asyncio

from common.app_logger import AppLogger
from common.contracts.database_models.enums import ImageKind
from common.contracts.messages import ContentGenerationRequested, ContentReadyForStyling
from common.providers import registry
from common.repositories.tenant_scoped import (
    ContentRepository,
    ImageRepository,
    NicheRepository,
    ProjectRepository,
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
                    self.logger.info(
                        f"Published ContentReadyForStyling for content {msg.content_id}"
                    )

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def __process_content_generation(
        self, tenant_id, integration_profile_id
    ) -> list[ContentReadyForStyling]:
        """Process content generation for an integration profile"""

        async with self.registry.get_database().get_session() as session:
            project_repo = ProjectRepository(session, tenant_id)
            niche_repo = NicheRepository(session, tenant_id)
            content_repo = ContentRepository(session, tenant_id)
            image_repo = ImageRepository(session, tenant_id)

            profile = await project_repo.get_integration_profile_by_id(
                integration_profile_id
            )
            if not profile:
                self.logger.error(
                    f"IntegrationProfile {integration_profile_id} not found"
                )
                return []

            niche = await niche_repo.get_by_id_with_keywords(profile.niche_id)
            if not niche:
                self.logger.error(f"Niche {profile.niche_id} not found")
                return []

            outgoing_msgs = []
            text_provider = self.registry.get_text_provider()

            for keyword in niche.keywords:
                try:
                    generated = text_provider.generate_text(
                        niche.title, keyword.term, str(profile.channel_id)
                    )

                    content = await content_repo.add(
                        niche_id=niche.external_id,
                        keyword_id=keyword.external_id,
                        title=generated.get("title", "[Untitled]"),
                        description=generated.get("description", "[No description]"),
                    )

                    image = await image_repo.add(
                        niche_id=niche.external_id,
                        keyword_id=keyword.external_id,
                        kind=ImageKind.ORIGINAL,
                    )

                    await session.commit()

                    outgoing_msgs.append(
                        ContentReadyForStyling(
                            tenant_id=tenant_id,
                            keyword_id=str(keyword.external_id),
                            niche_id=str(niche.external_id),
                            channel_id=str(profile.channel_id),
                            content_id=str(content.external_id),
                            base_image_id=str(image.external_id),
                        )
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error generating content for keyword '{keyword.term}': {e}"
                    )

            return outgoing_msgs

    def __get_logger(self):
        return AppLogger(__name__)
