import asyncio
from uuid import UUID

from common.app_logger import AppLogger
from common.contracts.database_models import Render
from common.contracts.database_models.enums import PublicationStatus
from common.contracts.messages import ContentReadyForPublication
from common.providers import registry
from common.repositories.cross_tenant import ChannelRepository
from common.repositories.tenant_scoped import (
    ContentRepository,
    PublicationRepository,
    RenderRepository,
)


class PublicationWorker:
    """Publication Worker - publishes content to distribution channels"""

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

                if not incoming_msg:
                    continue

                tenant_id = UUID(incoming_msg.tenant_id)
                content_id = UUID(incoming_msg.content_id)
                channel_id = UUID(incoming_msg.channel_id)
                render_id = UUID(incoming_msg.render_id)

                self.logger.info(
                    f"Received ContentReadyForPublication: tenant={tenant_id}, "
                    f"content={content_id}, channel={channel_id}, render={render_id}"
                )

                await self.__process_publication(
                    tenant_id, content_id, channel_id, render_id
                )

            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                await asyncio.sleep(1)

    async def __process_publication(
        self,
        tenant_id: UUID,
        content_id: UUID,
        channel_id: UUID,
        render_id: UUID,
    ) -> None:
        """Process publication for content"""

        async with self.registry.get_database().get_session() as session:
            content_repo = ContentRepository(session, tenant_id)
            publication_repo = PublicationRepository(session, tenant_id)
            render_repo = RenderRepository(session, tenant_id)
            channel_repo = ChannelRepository(session)

            # Step 3: Get content
            content = await content_repo.get_by_id(content_id)
            content_title = content.title
            content_desc = content.description
            self.logger.info(f"Fetched content: {content_title}")

            # Get channel to determine distribution channel provider
            channel_entity = await channel_repo.get_by_id(channel_id)
            distribution_channel = self.registry.get_channel(channel_entity.identifier)

            # Create publication record (pending status)
            publication = await publication_repo.add(
                channel_id=channel_id,
                content_id=content_id,
                render_id=render_id,
            )

            await session.commit()

            try:
                # Step 5: POST to channel (pinterest)
                self.logger.info(f"Publishing to channel: {channel_entity.identifier}")
                render: Render = await render_repo.get_by_id(render_id)
                render_uri = render.output_image_uri

                if not render_uri:
                    raise ValueError(f"Render URI empty for render Id: {render_id}")

                result = distribution_channel.publish(
                    title=content_title,
                    description=content_desc,
                    image_url=render_uri,
                )

                # Step 6: PinID returned
                post_id = result.get("post_id")
                self.logger.info(f"Publication successful, post_id: {post_id}")

                # Step 7: Record metadata - update publication with post_id
                await publication_repo.update_status(
                    publication.external_id,
                    PublicationStatus.PUBLISHED,
                    post_id=post_id,
                )
                await session.commit()

                self.logger.info(
                    f"Publication recorded: {publication.external_id} -> {post_id}"
                )

            except Exception as e:
                self.logger.error(f"Publication failed: {e}")
                await publication_repo.update_status(
                    publication.external_id,
                    PublicationStatus.FAILED,
                )
                await session.commit()
                raise

    def __get_logger(self):
        return AppLogger(__name__)
