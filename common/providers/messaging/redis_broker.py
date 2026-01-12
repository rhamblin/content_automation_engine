from typing import Optional
from common.app_logger import AppLogger
from common.contracts import IMessageBroker, IMessage

class RedisMessageBroker(IMessageBroker):
    """Redis implementation of IMessageBroker using async redis client"""
    def __init__(self, redis_client):
        self.logger = AppLogger(__name__)
        self.redis = redis_client

    async def consume(self, topic: type[IMessage]) -> Optional[IMessage]:
        """Consume a message from the specified topic"""
        message = await self.redis.blpop(topic.topic(), timeout=1)
        if message:
            topic_name, payload = message
            return topic.deserialize(payload)
        return None

    async def publish(self, message: IMessage) -> None:
        """Publish a message to the specified topic"""
        await self.redis.rpush(message.topic(), message.serialize())

    async def close(self):
        """Close the Redis connection"""
        await self.redis.close()