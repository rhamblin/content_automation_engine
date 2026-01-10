from common.contracts import IMessageBroker

class RedisMessageBroker(IMessageBroker):
    """Redis implementation of IMessageBroker"""
    def __init__(self, redis_client):
        self.redis = redis_client

    def consume(self, topic: str) -> dict:
        """Consume a message from the specified topic"""
        message = self.redis.blpop(topic)
        if message:
            return message
        return {}
    
    def publish(self, topic: str, payload: dict) -> None:
        """Publish a message to the specified topic"""
        self.redis.rpush(topic, payload)