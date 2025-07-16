from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from db_core.db_sync import get_db_session
from db_core.models.integration_profile import IntegrationProfile
from db_core.models.post import Post, PostStatus
from db_core.models.niche import Niche
from common.providers import registry
import json

broker = Redis(host="redis", port=6379)


def process_message():
    while True:
        result = broker.blpop("generate_post_queue", timeout=0)
        if result:
            _, message = result
            data = json.loads(message)
            profile_id = data.get("integration_profile_id")
            if profile_id:
                handle_job(profile_id)


def handle_job(profile_id: str):
    with get_db_session() as session:
        result = session.execute(
            select(IntegrationProfile)
            .options(selectinload(IntegrationProfile.niche).selectinload(Niche.keywords))
            .where(IntegrationProfile.integration_profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return
        keywords = [kw.keyword for kw in profile.niche.keywords]
        image_provider = registry.get_image_provider(profile.image_provider_key)
        model_provider = registry.get_model_provider(profile.model_provider_key)
        asset_url = image_provider.generate_image(", ".join(keywords))
        title = model_provider.generate_text(", ".join(keywords))
        description = model_provider.generate_text(", ".join(keywords))
        post = Post(
            integration_profile_id=profile.integration_profile_id,
            asset_url=asset_url,
            title=title,
            description=description,
            hashtags=keywords,
            status=PostStatus.ready
        )
        session.add(post)
        session.commit()
        broker.rpush("post_ready", json.dumps({"post_id": str(post.post_id)}))


if __name__ == "__main__":
    process_message()

