from common.contracts import MessageConsumer

class RedisMessageConsumer(MessageConsumer):
    """Redis implementation of MessageConsumer"""
    def __init__(self, redis_client):
        self.redis = redis_client

    def consume(self, topic: str) -> dict:
        """Consume a message from the specified topic"""
        message = self.redis.blpop(topic)
        if message:
            return message
        return {}