import json
import uuid
import asyncio
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from common.db_core.db_async import get_db_session
from common.db_core.models import IntegrationProfile, Post, PostStatus, Niche, Keyword
from common.providers import registry
from common.constants import constants

# Use async Redis client
broker = Redis(host="redis", port=6379)

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
                    print(f"[ERROR] Failed to process message {message}: {e}", flush=True)
        except Exception as e:
            print(f"[ERROR] Worker loop error: {e}", flush=True)
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
        for keyword in profile.niche.keywords:
             # Generate title and description
            generated_text = text_provider.generate_text(niche_name, keyword)
            title = generated_text.get("title", "")
            description = generated_text.get("description", "")

            image = getImage(niche_name, keyword)

            post = Post(
                integration_profile_id=profile.integration_profile_id,
                asset_url=image,
                title=title,
                description=description,
                hashtags=[kw.keyword for kw in profile.niche.keywords],
                status=PostStatus.ready,
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
            print(f"[JOB {job_id}] Pushed post {post.post_id} to {constants.POST_READY_BROKER_NAME}", flush=True)
        print(f"[JOB {job_id}] Completed post generation for profile {profile_id}", flush=True)

def getImage(niche_name, keyword):
    image_provider = registry.get_image_provider(keyword)
    image = image_provider.generate_image(f"image for niche {niche_name} and keyword {keyword.keyword}")
    return image.regular_url

async def main():
    """Entry point for the worker"""
    print("[INFO] Starting post worker...", flush=True)
    try:
        await process_message()
    except KeyboardInterrupt:
        print("[INFO] Worker shutting down...", flush=True)
    finally:
        await broker.close()

if __name__ == "__main__":
    asyncio.run(main())