import asyncio
from common.contracts import LocalMessage, MessageConsumer, IMessagePublisher, message_consumer, message_publisher
from common.providers import registry

class TemplateServiceWorker:
    """Template Worker Description"""
    def __init__(
            self, 
            registry: registry.ProviderRegistry,
            logger):
        self.registry = registry
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
