from redis.asyncio import Redis
import asyncio

from common.contracts.messages import LocalOutputMessage
from common.providers.messaging.redis_broker import RedisMessageBroker
from common.app_logger import AppLogger

async def consume_local_message():
    logger = AppLogger(__name__)
    logger.info("Consuming test message from Redis broker...")

    redis_instance = Redis(host="localhost", port=6379)
    message_broker = RedisMessageBroker(redis_instance)

    payload = await message_broker.consume(LocalOutputMessage)
    logger.info(f"Message consumed successfully. Here you go: {payload}")

asyncio.run(consume_local_message())


