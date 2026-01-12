from common.app_logger import AppLogger
from common.contracts import IMessageBroker, IMessage

class RedisMessageBroker(IMessageBroker):
    """Redis implementation of IMessageBroker"""
    def __init__(self, redis_client):
        self.logger = AppLogger(__name__)
        self.redis = redis_client

    def consume(self, topic: type[IMessage]) -> IMessage:
        """Consume a message from the specified topic"""
        message = self.redis.blpop(topic.topic())
        if message:
            topic_name, payload = message
            return topic.deserialize(payload)
        return None

    def publish(self, message: IMessage) -> None:
        """Publish a message to the specified topic"""
        self.redis.rpush(message.topic(), message.serialize())