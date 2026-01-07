import json
import uuid
import asyncio
from datetime import datetime

from sqlalchemy import select

from common.db_core.models import Content, ContentPublication, PublicationStatus
from common.constants import constants

class PublicationWorker:
    """Worker to publish content to channels based on messages from Redis queue"""
    def __init__(self, redis_broker, db_session_factory, provider_registry, logger):
        self.broker = redis_broker
        self.db_session_factory = db_session_factory
        self.provider_registry = provider_registry
        self.logger = logger

    async def process_message(self) -> None:
        """Main worker loop - processes messages from Redis queue"""
        while True:
            try:
                # Use async blpop
                result = await self.broker.blpop(
                    f"{constants.PREFIX_CONTENT_READY_FOR_PUBLICATION_QUEUE}{constants.CHANNEL_PINTEREST}",
                    timeout=0
                )
                if result:
                    _, message = result
                    try:
                        payload = json.loads(message)
                        content_id = payload.get("content_id")
                        channel_key = payload.get("channel_key")
                        await self.publish_content(content_id, channel_key)
                    except Exception as e:
                        self.logger.error(f"Failed to process message {message}: {e}")
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    async def publish_content(self, content_id: str, channel_key: str) -> None:
        """Publish content to the specified channel"""
        async with self.db_session_factory() as session:
            # Fetch content from database
            result = await session.execute(
                select(Content).where(Content.content_id == uuid.UUID(content_id))
            )
            content = result.scalar_one_or_none()

            if not content:
                self.logger.error(f"Content {content_id} not found")
                return

            # Create publication record
            publication = ContentPublication(
                content_id=content.content_id,
                channel_key=channel_key,
                status=PublicationStatus.PUBLISHING.value
            )
            session.add(publication)
            await session.commit()
            await session.refresh(publication)

            try:
                # Get channel provider
                channel = self.provider_registry.get_channel(channel_key)

                # Publish to channel
                result = channel.publish(
                    title=content.title,
                    description=content.description,
                    image_url=content.asset_url,
                    hashtags=content.hashtags
                )

                # Update publication record with success
                publication.status = PublicationStatus.PUBLISHED.value
                publication.platform_post_id = result.get("post_id") if isinstance(result, dict) else "unknown"
                publication.published_at = datetime.utcnow()
                publication.platform_metadata = result if isinstance(result, dict) else {}

                await session.commit()

                self.logger.info(
                    f"Successfully published content {content_id} to {channel_key}. "
                    f"Post ID: {publication.platform_post_id}"
                )

            except Exception as e:
                # Update publication record with failure
                publication.status = PublicationStatus.FAILED.value
                publication.platform_metadata = {"error": str(e)}
                await session.commit()

                self.logger.error(f"Failed to publish content {content_id} to {channel_key}: {e}")
