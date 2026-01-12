from redis.asyncio import Redis
import asyncio

from common.contracts import LocalInputMessage
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.app_logger import AppLogger

async def publish_local_message():
    logger = AppLogger(__name__)
    logger.info("Pushing test message to Redis broker...")

    redis_instance = Redis(host="localhost", port=6379)
    message_broker = RedisMessageBroker(redis_instance)

    payload = LocalInputMessage(message="This is DevTools. Are you there?")

    await message_broker.publish(payload)
    logger.info(f"Message published successfully. Message content: {payload}")

asyncio.run(publish_local_message())


