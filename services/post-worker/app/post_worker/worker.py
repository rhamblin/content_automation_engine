import json
import uuid
import asyncio
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db_core.db_async import get_db_session
from db_core.models import IntegrationProfile, Post, PostStatus, Niche, Keyword
from providers import registry
from constants import constants

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

        # Get providers
        image_provider = registry.get_image_provider(profile.image_provider_key)
        text_provider = registry.get_text_provider(profile.text_provider_key)

        # Generate content (add await if these are async)
        keywords = ", ".join(kw.keyword for kw in profile.niche.keywords)
        title = await text_provider.generate_text(f"title for {profile.niche.name} {keywords}")
        description = await text_provider.generate_text(f"description for {profile.niche.name} {keywords}")
        image = await image_provider.generate_image(f"image for niche {profile.niche.name}")

        # # Create and save post
        # post = Post(
        #     integration_profile_id=profile.integration_profile_id,
        #     asset_url=image,  # Use the generated image
        #     title=title,
        #     description=description,
        #     hashtags=[kw.keyword for kw in profile.niche.keywords],
        #     status=PostStatus.ready,
        # )
        # session.add(post)
        # await session.commit()  # Add await for commit
        # await session.refresh(post)  # Add await for refresh

        # Push to next queue using async Redis
        await broker.rpush(
            constants.POST_READY_BROKER_NAME, 
            json.dumps({"post_id": str(post.post_id)})
        )
        print(f"[JOB {job_id}] Generated post {post.post_id}", flush=True)

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