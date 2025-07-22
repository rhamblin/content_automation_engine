import json
import uuid
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db_core.db_sync import get_db_session
from db_core.models import IntegrationProfile, Post, PostStatus, Niche, Keyword
from providers import registry
from constants import constants

broker = Redis(host="redis", port=6379)


def process_message() -> None:
    while True:
        result = broker.blpop(constants.GENERATE_POST_QUEUE_NAME, timeout=0)
        if result:
            _, message = result
            try:
                payload = json.loads(message)
                profile_id = payload.get("integration_profile_id")
                job_id = payload.get("job_id")
                generate_post(job_id, profile_id)
            except Exception as e:
                print(f"[ERROR] Failed to process message {message}: {e}", flush=True)


def generate_post(job_id: str, profile_id: str) -> None:
    with get_db_session() as session:
        result = session.execute(
            select(IntegrationProfile)
            .options(
                selectinload(IntegrationProfile.niche).selectinload(Niche.keywords)
            )
            .where(IntegrationProfile.integration_profile_id == uuid.UUID(profile_id))
        )
        profile = result.scalar_one()

        image_provider = registry.get_image_provider(profile.image_provider_key)
        text_provider = registry.get_text_provider(profile.text_provider_key)

        keywords = ", ".join(kw.keyword for kw in profile.niche.keywords)
        title = text_provider.generate_text(f"title for {profile.niche.name} {keywords}")
        description = text_provider.generate_text(f"description for {profile.niche.name} {keywords}")
        # image_url = image_provider.generate_image(f"image for niche {profile.niche.name}")

        post = Post(
            integration_profile_id=profile.integration_profile_id,
            asset_url="fdfd",#image_url,
            title=title,
            description=description,
            hashtags=[kw.keyword for kw in profile.niche.keywords],
            status=PostStatus.ready,
        )
        session.add(post)
        session.commit()
        session.refresh(post)

        broker.rpush(constants.POST_READY_BROKER_NAME, json.dumps({"post_id": str(post.post_id)}))
        print(f"[JOB {job_id}] Generated post {post.post_id}", flush=True)


if __name__ == "__main__":
    process_message()
