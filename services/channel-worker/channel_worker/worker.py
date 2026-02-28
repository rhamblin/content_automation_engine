import asyncio
from io import BytesIO
from uuid import UUID

from PIL import Image

from common.app_logger import AppLogger
from common.contracts.database_models.enums import PublicationStatus, RenderStatus
from common.contracts.messages import ContentGenerationRequested
from common.providers import registry
from common.repositories.cross_tenant import ChannelRepository
from common.utils.string_utils import to_camel_case
from common.repositories.tenant_scoped import (
    ContentRepository,
    IntegrationProfileRepository,
    NicheRepository,
    PublicationRepository,
    RenderRepository,
)


class ChannelWorker:
    """Consolidated Channel Worker - generates, renders, and publishes content."""

    def __init__(self, registry: registry.ProviderRegistry):
        self.logger = self.__get_logger()
        self.registry = registry

    async def work(self) -> None:
        """Main worker loop."""
        self.logger.info("ChannelWorker started.")

        while True:
            try:
                incoming_msg: ContentGenerationRequested = (
                    await self.registry.get_message_broker().consume(
                        ContentGenerationRequested
                    )
                )

                if not incoming_msg:
                    continue

                tenant_id = UUID(incoming_msg.tenant_id)
                integration_profile_id = UUID(incoming_msg.integration_profile_id)

                self.logger.info(
                    f"Received ContentGenerationRequested: tenant={tenant_id}, "
                    f"integration_profile={integration_profile_id}"
                )

                await self._process(tenant_id, integration_profile_id)

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def _process(
        self, tenant_id: UUID, integration_profile_id: UUID
    ) -> None:
        """Process content generation, rendering, and publication for an integration profile."""

        async with self.registry.get_database().get_session() as session:
            profile_repo = IntegrationProfileRepository(session, tenant_id)
            niche_repo = NicheRepository(session, tenant_id)
            content_repo = ContentRepository(session, tenant_id)
            render_repo = RenderRepository(session, tenant_id)
            publication_repo = PublicationRepository(session, tenant_id)
            channel_repo = ChannelRepository(session)

            profile = await profile_repo.get_by_id(integration_profile_id)
            niche = await niche_repo.get_by_id_with_keywords(profile.niche_id)
            channel_entity = await channel_repo.get_by_id(profile.channel_id)
            distribution_channel = self.registry.get_channel(channel_entity.identifier)
            llm = self.registry.get_llm()
            blob_storage = self.registry.get_blob_storage()

            for keyword in niche.keywords:
                try:
                    # 1. GENERATE - call LLM provider
                    generated = llm.generate(
                        niche.title,
                        keyword.term,
                        distribution_channel,
                        persona_prompt=niche.persona_prompt,
                        audience_prompt=niche.audience_prompt,
                    )

                    content = await content_repo.add(
                        niche_id=niche.external_id,
                        keyword_id=keyword.external_id,
                        title=generated.get("title", "[Untitled]"),
                        description=generated.get("description", "[No description]"),
                    )

                    self.logger.info(
                        f"Generated content for keyword '{keyword.term}': {content.external_id}"
                    )

                    # 2. RENDER - fetch image and render content
                    input_image_uri = blob_storage.fetch_image_uri(keyword)

                    render = await render_repo.add(
                        content_id=content.external_id,
                        niche_id=niche.external_id,
                        keyword_id=keyword.external_id,
                        input_image_uri=input_image_uri,
                    )

                    # Fetch source image and render
                    source_image = await self._fetch_image(input_image_uri)
                    if source_image:
                        rendered_image = distribution_channel.render_content(
                            source=source_image,
                            text_data=generated,
                            style=None,
                        )

                        # Upload rendered image and update render record
                        output_uri = await self._upload_rendered_image(
                            rendered_image, keyword.term, render.external_id
                        )
                        render.output_image_uri = output_uri
                        render.status = RenderStatus.COMPLETED
                    else:
                        self.logger.warning(
                            f"Could not fetch source image for keyword '{keyword.term}'"
                        )
                        render.status = RenderStatus.FAILED
                        await session.commit()
                        continue

                    self.logger.info(
                        f"Rendered content for keyword '{keyword.term}': {render.external_id}"
                    )

                    # 3. PUBLISH - create publication and post to channel
                    publication = await publication_repo.add(
                        channel_id=profile.channel_id,
                        content_id=content.external_id,
                        render_id=render.external_id,
                    )

                    try:
                        tags = [to_camel_case(t) for t in [niche.title, keyword.term]]
                        result = distribution_channel.publish(
                            title=content.title,
                            description=content.description,
                            content=render.output_image_uri,
                            tags=tags,
                        )

                        post_id = result.get("post_id")
                        await publication_repo.update_status(
                            publication.external_id,
                            PublicationStatus.PUBLISHED,
                            post_id=post_id,
                        )

                        self.logger.info(
                            f"Published content for keyword '{keyword.term}': post_id={post_id}"
                        )

                    except Exception as e:
                        self.logger.error(f"Publication failed for '{keyword.term}': {e}")
                        await publication_repo.update_status(
                            publication.external_id,
                            PublicationStatus.FAILED,
                        )

                    await session.commit()

                except Exception as e:
                    self.logger.error(
                        f"Error processing keyword '{keyword.term}': {e}"
                    )
                    await session.rollback()

    async def _fetch_image(self, uri: str) -> Image.Image | None:
        """Fetch image from blob storage."""
        try:
            blob_storage = self.registry.get_blob_storage()
            image_bytes = blob_storage.download_blob(uri)
            return Image.open(BytesIO(image_bytes))
        except Exception as e:
            self.logger.error(f"Failed to fetch image from {uri}: {e}")
            return None

    async def _upload_rendered_image(
        self, image: Image.Image, keyword_term: str, render_id: UUID
    ) -> str:
        """Upload rendered image to blob storage and return URI."""
        try:
            blob_storage = self.registry.get_blob_storage()
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            blob_name = f"renders/{render_id}.png"
            blob_storage.upload_blob(blob_name, buffer.getvalue())
            return blob_name
        except Exception as e:
            self.logger.error(f"Failed to upload rendered image: {e}")
            raise

    def __get_logger(self):
        return AppLogger(__name__)
