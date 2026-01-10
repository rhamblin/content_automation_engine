from common.contracts import IMessagePublisher

class RedisMessagePublisher(IMessagePublisher):
    """Redis implementation of MessagePublisher"""
    def __init__(self, redis_client):
        self.redis = redis_client

    def publish(self, topic: str, payload: dict) -> None:
        """Publish a message to the specified topic"""
        self.redis.rpush(topic, payload)
