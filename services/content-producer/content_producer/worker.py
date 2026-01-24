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

                if incoming_msg:

                    tenant_id, project_id = (
                        incoming_msg.tenant_id,
                        incoming_msg.project_id,
                    )

                    self.logger.info(
                        f"Received ContentGenerationRequested: tenant={tenant_id}, "
                        f"project={project_id}"
                    )
                    await self.__process_content_generation(tenant_id, project_id)

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def __process_content_generation(self, tenant_id, project_id) -> None:
        """Process content generation for a project's integration profiles"""

        async with self.registry.get_database().get_session() as session:
            project_repo = ProjectRepository(session, tenant_id)
            niche_repo = NicheRepository(session, tenant_id)
            content_repo = ContentRepository(session, tenant_id)
            image_repo = ImageRepository(session, tenant_id)

            project = await project_repo.get_by_id_with_profiles(project_id)
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return

            for profile in project.integration_profiles:
                if not profile.is_active:
                    continue

                niche = await niche_repo.get_by_id_with_keywords(profile.niche_id)
                if not niche:
                    self.logger.error(f"Niche {profile.niche_id} not found")
                    continue

                text_provider = self.registry.get_text_provider()

                for keyword in niche.keywords:
                    if not keyword.is_active:
                        continue

                    try:
                        generated = text_provider.generate_text(
                            niche.title, keyword.term, str(profile.channel_id)
                        )

                        content = await content_repo.add(
                            niche_id=niche.external_id,
                            keyword_id=keyword.external_id,
                            title=generated.get("title", "[Untitled]"),
                            description=generated.get(
                                "description", "[No description]"
                            ),
                        )

                        image = await image_repo.add(
                            niche_id=niche.external_id,
                            keyword_id=keyword.external_id,
                            kind=ImageKind.ORIGINAL,
                        )

                        outgoing_msg = ContentReadyForStyling(
                            tenant_id=msg.tenant_id,
                            keyword_id=str(keyword.external_id),
                            niche_id=str(niche.external_id),
                            channel_id=str(profile.channel_id),
                            content_id=str(content.external_id),
                            base_image_id=str(image.external_id),
                        ).chain_from(msg)

                        await self.registry.get_message_broker().publish(outgoing_msg)
                        self.logger.info(
                            f"Published ContentReadyForStyling for content {content.external_id}"
                        )

                    except Exception as e:
                        self.logger.error(
                            f"Error generating content for keyword '{keyword.term}': {e}"
                        )

            await session.commit()

    def __get_logger(self):
        return AppLogger(__name__)
