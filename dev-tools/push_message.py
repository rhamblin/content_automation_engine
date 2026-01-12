import redis
import asyncio

from common.contracts import LocalInputMessage
from common.providers.messaging.redis_broker import RedisMessageBroker 
from common.app_logger import AppLogger

async def push_local_message():
    logger = AppLogger(__name__)
    logger.info("Pushing test message to Redis broker...")

    redis_instance = redis.Redis(host="redis", port=6379)
    message_broker = RedisMessageBroker(redis_instance)

    payload = LocalInputMessage(message="Are you there?")

    await message_broker.publish(payload)
    logger.info("Message published successfully.")

asyncio.run(push_local_message())


