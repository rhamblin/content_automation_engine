import json
import uuid
import asyncio
import logging

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from common.db_core.db_async import get_db_session
from common.db_core.models import IntegrationProfile, Post, PostStatus, Niche, Keyword
from common.providers import registry
from common.constants import constants
from common.observability.logging_config import configure_logging

# Use async Redis client
broker = Redis(host="redis", port=6379)

logger = logging.getLogger(__name__)

async def process_message() -> None:
    """Main worker loop - processes messages from Redis queue"""
    while True:
        try:
            # Use async blpop
            result = await broker.blpop(constants.GENERATE_POST_QUEUE_NAME, timeout=0)
            if result:
                _, message = result
                try:
                    payload = json.loads(message)
                    profile_id = payload.get("integration_profile_id")
                    job_id = payload.get("job_id")
                    await generate_post(job_id, profile_id)
                except Exception as e:
                    logger.error(f"Failed to process message {message}: {e}")
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(1)  # Brief pause before retrying

async def generate_post(job_id: str, profile_id: str) -> None:
    """Generate a post for the given integration profile"""
    async with get_db_session() as session:
        # Add await for async database query
        result = await session.execute(
            select(IntegrationProfile)
            .options(
                selectinload(IntegrationProfile.niche).selectinload(Niche.keywords)
            )
            .where(IntegrationProfile.integration_profile_id == uuid.UUID(profile_id))
        )
        profile = result.scalar_one()

        text_provider = registry.get_text_provider(profile.text_provider_key)

        niche_name = profile.niche.name
        channel = profile.channel_key
        for kw in profile.niche.keywords:
            keyword = kw.keyword
             # Generate title and description
            generated_text = ""
            try:
                generated_text = text_provider.generate_text(niche_name, keyword, channel)
            except Exception as e:
                logger.error(f"Text generation failed for keyword {keyword} in profile {profile_id}: {e}")
                continue

            title = generated_text.get("title", "")
            description = generated_text.get("description", "")

            # image = getImage(niche_name, keyword)

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
            await broker.rpush(
                constants.POST_READY_BROKER_NAME,
                json.dumps({
                    "post_id": str(post.post_id),
                    "channel_key": profile.channel_key
                })
            )
            logger.info(f"[JOB {job_id}] Pushed post {post.post_id} to {constants.POST_READY_BROKER_NAME}")
        logger.info(f"[JOB {job_id}] Completed post generation for profile {profile_id}")

def getImage(niche_name: str, keyword: str):
    image_provider = registry.get_image_provider(keyword)
    image = image_provider.generate_image(niche_name, keyword)
    return image.regular_url

async def main():
    """Entry point for the worker"""
    logger.info("Starting post worker...")
    try:
        await process_message()
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
    finally:
        await broker.close()

if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())