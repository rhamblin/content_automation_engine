from typing import Optional

from redis.exceptions import RedisError

from common.app_logger import AppLogger
from common.contracts.interfaces import IMessageBroker, IMessage


class RedisMessageBroker(IMessageBroker):
    """Redis implementation of IMessageBroker using async redis client"""

    def __init__(self, redis_client):
        self.logger = AppLogger(__name__)
        self.redis = redis_client

    async def consume(self, topic: type[IMessage]) -> Optional[IMessage]:
        """Consume a message from the specified topic."""
        try:
            message = await self.redis.blpop(topic.topic(), timeout=1)
        except RedisError as e:
            raise ConnectionError(f"Failed to consume from Redis: {e}") from e

        if message:
            topic_name, payload = message
            return topic.deserialize(payload)
        return None

    async def publish(self, message: IMessage) -> None:
        """Publish a message to the specified topic."""
        try:
            await self.redis.rpush(message.topic(), message.serialize())
        except RedisError as e:
            raise ConnectionError(f"Failed to publish to Redis: {e}") from e

    async def close(self):
        """Close the Redis connection."""
        try:
            await self.redis.close()
        except RedisError as e:
            raise ConnectionError(f"Failed to close Redis connection: {e}") from e