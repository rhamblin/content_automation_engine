import asyncio
from common.messaging_contracts import LocalMessage

class TemplateServiceWorker:
    """Worker to generate content based on messages from Redis queue"""
    def __init__(self, redis_broker, logger):
        self.broker = redis_broker
        self.logger = logger

    async def process_message(self) -> None:
        """Main worker loop - processes messages from Redis queue"""
        message_name = LocalMessage.message_name()
        payload = LocalMessage(message=f"Hello from {self.__class__.__name__ }!")
        while True:
            try:
                # Use async blpop
                result = await self.broker.blpop(message_name, timeout=0)
                if result:
                    _, message = result
                    try:
                        payload = LocalMessage.from_json(message)
                        self.logger.info(f"Received message: {payload.message}")
                    except Exception as e:
                        self.logger.error(f"Failed to process message {message}: {e}")
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
