import json
import uuid
import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from common.db_core.models import IntegrationProfile, Post, PostStatus, Niche, Keyword
from common.constants import constants

class PostWorker:
    """Worker to generate posts based on messages from Redis queue"""
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
                result = await self.broker.blpop(constants.GENERATE_POST_QUEUE_NAME, timeout=0)
                if result:
                    _, message = result
                    try:
                        payload = json.loads(message)
                        profile_id = payload.get("integration_profile_id")
                        job_id = payload.get("job_id")
                        await self.generate_post(job_id, profile_id)
                    except Exception as e:
                        self.logger.error(f"Failed to process message {message}: {e}")
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    async def generate_post(self,job_id: str, profile_id: str) -> None:
        """Generate a post for the given integration profile"""
        async with self.db_session_factory() as session:
            # Add await for async database query
            result = await session.execute(
                select(IntegrationProfile)
                .options(
                    selectinload(IntegrationProfile.niche).selectinload(Niche.keywords)
                )
                .where(IntegrationProfile.integration_profile_id == uuid.UUID(profile_id))
            )
            profile = result.scalar_one()

            # Text provider is hardcoded to Azure Foundry
            text_provider = self.provider_registry.get_text_provider()

            niche_name = profile.niche.name
            channel = profile.channel_key
            for kw in profile.niche.keywords:
                keyword = kw.name
                # Generate title and description
                generated_text = text_provider.generate_text(niche_name, keyword, channel)
                title = generated_text.get("title", "")
                description = generated_text.get("description", "")

                # image_url = self.fetch_image_url(niche_name, kw)

                post = Post(
                    integration_profile_id=profile.integration_profile_id,
                    asset_url="dummy_image_url",  # Placeholder for image URL
                    title=title,
                    description=description,
                    hashtags=[f"#{keyword}"],
                    status=PostStatus.ready.value,
                )

                session.add(post)
                await session.commit()

                # Push to next queue using async Redis
                await self.broker.rpush(
                    constants.POST_READY_BROKER_NAME,
                    json.dumps({
                        "post_id": str(post.post_id),
                        "channel_key": profile.channel_key
                    })
                )
                self.logger.info(f"[JOB {job_id}] Pushed post {post.post_id} to {constants.POST_READY_BROKER_NAME}")
            self.logger.info(f"[JOB {job_id}] Completed post generation for profile {profile_id}")

    def getImage(self, niche_name: str, key: str):
        image_provider = self.provider_registry.get_image_provider()
        image = image_provider.fetch_image(niche_name, key)
        return image.regular_url